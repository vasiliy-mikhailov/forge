"""Minimal Stage-1 agent loop for reward-bench.

Lighter than OpenHands: a single-purpose script that gives the candidate
LLM enough tools to write and iterate on /workspace/submission.py.

Flow per turn:
    1. Send chat-completion request to /v1/chat/completions
       (the shim, or vLLM, or any OpenAI-compatible backend).
    2. Parse the model's reply for tool calls.
    3. Execute the tool calls in /workspace and /tasks (read-only).
    4. Append observation to the message history.
    5. Loop until 'finish' tool is called, or budget exhausted
       (max iterations / max wall).

Tools exposed (XML-tagged for simplicity — easier to parse than the
OpenAI tool-call protocol while still being legible to most chat models):

    <tool name="view"><path>/path/to/file</path></tool>
        Print the contents of file (read-only).

    <tool name="write_file"><path>/workspace/submission.py</path><content>
        ...code...
    </content></tool>
        Overwrite the file at <path> with <content>.

    <tool name="bash"><cmd>python /tasks/2048/dev_runner.py /workspace/submission.py</cmd></tool>
        Run a shell command (limited to allow-list: python, ls, cat, head).

    <tool name="finish"><note>brief reason</note></tool>
        Declare done. Stops the loop. Final submission.py is what gets scored.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


# ----- Tool dispatcher -----

ALLOWED_BASH_PREFIXES = (
    "python /tasks/2048/dev_runner.py /workspace/submission.py",
    "python3 /tasks/2048/dev_runner.py /workspace/submission.py",
    "ls /workspace",
    "ls /tasks",
    "ls /env",
    "cat /workspace/submission.py",
    "head /workspace/submission.py",
    "cat /tasks/2048/SKILL_tier1.md",
    "cat /env/env_2048.py",
)


def _trim(s: str, n: int = 4000) -> str:
    if len(s) <= n:
        return s
    return s[: n - 200] + f"\n... [truncated, total {len(s)} chars]"


# ----- Virtual → host path remapping -----
# The model thinks it is operating on /workspace, /env, /tasks. We remap to
# the actual host directories the operator passed via CLI flags. This keeps
# the prompt portable across attempts (which live under different host paths)
# and matches the canonical-eval sandbox's path layout.

def _virt_to_host(virt: str, workspace: Path, env_dir: Path, tasks_dir: Path) -> Path | None:
    """Resolve a model-supplied virtual path to a host path. Returns None if
    the path doesn't sit under one of the allowed virtual roots."""
    if not virt:
        return None
    p = virt.strip()
    # Normalise: strip any trailing slash, collapse double slashes
    while "//" in p:
        p = p.replace("//", "/")
    for prefix, root in (("/workspace", workspace), ("/env", env_dir), ("/tasks", tasks_dir)):
        if p == prefix or p.startswith(prefix + "/"):
            tail = p[len(prefix):].lstrip("/")
            host = (root / tail).resolve() if tail else root.resolve()
            # Defence-in-depth: post-resolve check to block ../ escapes
            if not str(host).startswith(str(root.resolve())):
                return None
            return host
    return None


def _host_to_virt(host: Path, workspace: Path, env_dir: Path, tasks_dir: Path) -> str:
    """Best-effort reverse map (used only for echoing paths back)."""
    h = str(host.resolve())
    for prefix, root in (("/workspace", workspace), ("/env", env_dir), ("/tasks", tasks_dir)):
        rs = str(root.resolve())
        if h == rs:
            return prefix
        if h.startswith(rs + "/"):
            return prefix + "/" + h[len(rs) + 1:]
    return h


def execute_tool(name: str, args: dict[str, str], workspace: Path, env_dir: Path, tasks_dir: Path) -> str:
    """Run one tool. Returns observation text the model will see next turn."""
    if name == "view":
        virt = args.get("path", "")
        host = _virt_to_host(virt, workspace, env_dir, tasks_dir)
        if host is None:
            return f"<error>view: path must start with /workspace, /env, or /tasks (got {virt!r})</error>"
        if not host.exists():
            return f"<error>view: file not found: {virt}</error>"
        try:
            return f"<view path=\"{virt}\">\n{_trim(host.read_text())}\n</view>"
        except Exception as e:
            return f"<error>view: {e}</error>"

    if name == "write_file":
        virt = args.get("path", "")
        content = args.get("content", "")
        host = _virt_to_host(virt, workspace, env_dir, tasks_dir)
        if host is None:
            return f"<error>write_file: path must start with /workspace (got {virt!r})</error>"
        if not str(host).startswith(str(workspace.resolve())):
            return f"<error>write_file: writes only allowed under /workspace (got {virt!r})</error>"
        host.parent.mkdir(parents=True, exist_ok=True)
        host.write_text(content)
        return f"<ok>wrote {len(content)} chars to {virt}</ok>"

    if name == "bash":
        virt_cmd = args.get("cmd", "").strip()
        if not any(virt_cmd.startswith(p) for p in ALLOWED_BASH_PREFIXES):
            return f"<error>bash: command not on allow-list. Allowed prefixes:\n" + "\n".join(f"  {p}" for p in ALLOWED_BASH_PREFIXES) + f"\nReceived: {virt_cmd}</error>"
        # Translate virtual paths inside the command. Order matters: longer first.
        cmd = virt_cmd
        for prefix, root in (("/workspace", workspace), ("/tasks", tasks_dir), ("/env", env_dir)):
            cmd = cmd.replace(prefix, str(root.resolve()))
        # Make `import env_2048` resolve to env_dir/env_2048.py inside dev_runner.
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{env_dir.resolve()}:" + env.get("PYTHONPATH", "")
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=120,
                cwd=str(workspace), env=env,
            )
            stdout = _trim(result.stdout)
            stderr = _trim(result.stderr)
            return f"<bash exit={result.returncode}>\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n</bash>"
        except subprocess.TimeoutExpired:
            return f"<error>bash: timed out after 120s</error>"
        except Exception as e:
            return f"<error>bash: {e}</error>"

    if name == "finish":
        note = args.get("note", "")
        return f"<finish>{note}</finish>"

    return f"<error>unknown tool: {name}</error>"


# ----- Tool-call parser -----
#
# Format: a single fenced ```tool block per call. The block has two regions
# separated by a line containing only `---`:
#
#   1. JSON args   — small, machine-readable
#   2. Body text   — optional, used as `content` for write_file. Raw, no
#                    escaping required (this is the whole point — keeps
#                    multi-KB Python files in O(file_size) tokens).
#
# Example with body:
#   ```tool
#   {"name": "write_file", "args": {"path": "/workspace/submission.py"}}
#   ---
#   from __future__ import annotations
#   import math
#   ... raw code ...
#   ```
#
# Example without body:
#   ```tool
#   {"name": "view", "args": {"path": "/env/env_2048.py"}}
#   ```

def _detokenize_bpe(s):
    """Strip BPE byte-pair markers that some Mistral/Pixtral quants leak.
    Ga (U+0120) is leading-space; Cnewline (U+010A) is newline.
    Proper detokenizer should convert these but doesn't for HF-format
    Mistral quants without --tokenizer-mode mistral."""
    if not s:
        return s
    return s.replace("\u0120", " ").replace("\u010a", "\n").replace("\u0109", "\t")


_TOOL_BLOCK_RE = re.compile(r"```tool\b\s*(.*?)\s*```", re.DOTALL)
# Fallback: an unclosed ```tool block at the end of the reply. Some models
# (notably Qwen 3.6) hit a practical generation cap around ~9 KB and stop
# emitting tokens before they reach the closing fence. This still gives us
# a parseable tool call most of the time — better than dropping the turn.
_TOOL_BLOCK_TRAILING_RE = re.compile(r"```tool\b\s*(.*)\Z", re.DOTALL)
_BODY_SPLIT_RE = re.compile(r"\n(?:===FILE_BODY===|---)\s*\n", re.DOTALL)


def parse_tool_calls(text: str) -> list[tuple[str, dict[str, str]]]:
    out: list[tuple[str, dict[str, str]]] = []
    consumed_end = 0
    for m in _TOOL_BLOCK_RE.finditer(text):
        consumed_end = m.end()
        raw = m.group(1)
        # Split args region from optional body region on `---` line.
        parts = _BODY_SPLIT_RE.split(raw, maxsplit=1)
        json_part = parts[0].strip()
        body_part = parts[1] if len(parts) == 2 else None
        try:
            obj = json.loads(json_part)
        except json.JSONDecodeError:
            try:
                obj = json.loads(json_part.rstrip(", \t\n"))
            except json.JSONDecodeError:
                continue
        if not isinstance(obj, dict):
            continue
        name = str(obj.get("name", "")).strip()
        if not name:
            continue
        args = obj.get("args", {})
        if not isinstance(args, dict):
            args = {}
        norm: dict[str, str] = {}
        for k, v in args.items():
            if isinstance(v, str):
                norm[k] = v
            else:
                norm[k] = json.dumps(v)
        # Body region attached as `content` if write_file didn't pass one.
        if body_part is not None:
            # Strip the trailing artifacts the model sometimes leaves behind
            # (XML-ish closing tags from pretraining data — </write_file>,
            # </content>, </tool>) so they don't end up inside the file.
            body_part = re.sub(
                r"(\n*</[a-zA-Z_][a-zA-Z0-9_]*>\s*|\s)+\Z",
                "", body_part)
            if name == "write_file" and "content" not in norm:
                norm["content"] = body_part
            else:
                norm.setdefault("body", body_part)
        out.append((name, norm))

    # Fallback: if no closed tool block matched AT ALL but the reply ends
    # with an unclosed ```tool block, treat that as one. Catches Qwen-3.6's
    # generation-cap truncation where the closing fence never lands.
    if not out:
        m = _TOOL_BLOCK_TRAILING_RE.search(text)
        if m:
            raw = m.group(1)
            parts = _BODY_SPLIT_RE.split(raw, maxsplit=1)
            json_part = parts[0].strip()
            body_part = parts[1] if len(parts) == 2 else None
            try:
                obj = json.loads(json_part)
            except json.JSONDecodeError:
                obj = None
            if isinstance(obj, dict):
                name = str(obj.get("name", "")).strip()
                args = obj.get("args", {})
                if name and isinstance(args, dict):
                    norm: dict[str, str] = {}
                    for k, v in args.items():
                        norm[k] = v if isinstance(v, str) else json.dumps(v)
                    if body_part is not None and name == "write_file":
                        # Strip trailing artifacts the model emits when it
                        # runs out of generation budget mid-block:
                        #   - partial closing code fence ``` or ``
                        #   - XML-ish closing tags from training data
                        #     (</write_file>, </content>, </tool>, etc.)
                        #   - whitespace
                        body_part = re.sub(
                            r"(\n```\s*|\n*</[a-zA-Z_][a-zA-Z0-9_]*>\s*|\s)+\Z",
                            "", body_part)
                        norm.setdefault("content", body_part)
                    out.append((name, norm))
    return out


# ----- LLM client -----

def _approx_tokens(messages: list[dict]) -> int:
    """Cheap char-based estimate. Real tokenisation depends on the model;
    4 chars ≈ 1 token is a conservative upper bound for English/code."""
    total = 0
    for m in messages:
        c = m.get("content", "")
        if isinstance(c, str):
            total += len(c)
    return total // 4


def _prune_history(messages: list[dict], target_tokens: int) -> list[dict]:
    """Keep system + first user + last assistant/observation pairs whose
    cumulative token count fits target_tokens. Older middle turns are
    dropped (replaced with a single placeholder note)."""
    if _approx_tokens(messages) <= target_tokens:
        return messages
    if len(messages) < 4:
        return messages
    head = messages[:2]  # system + first user
    tail = messages[2:]
    # Keep the most recent N pairs that still fit; pop oldest until under target.
    while _approx_tokens(head + tail) > target_tokens and len(tail) > 2:
        # Drop two messages (assistant + observation) from the front of the tail.
        tail = tail[2:]
    placeholder = {
        "role": "user",
        "content": "<note>Earlier turns were pruned to keep the conversation under the context-length watchdog. Your current submission is still on disk at /workspace/submission.py — view it if you need to refresh your memory.</note>",
    }
    return head + [placeholder] + tail


def call_llm(base_url: str, api_key: str, model: str, messages: list[dict],
             temperature: float = 0.0, max_tokens: int = 12288,
             seed: int | None = None) -> str:
    """POST to an OpenAI-compat /v1/chat/completions endpoint.

    max_tokens is set explicitly because some servers (incl. vLLM with default
    config) cap completions at a small number that truncates tool calls
    mid-tag.

    tool_choice="none" disables vLLM's auto-tool-choice parser, which
    otherwise intercepts our XML-style <tool name="…"> blocks (Qwen's tool
    parser collides with our convention). We do our own parsing in
    parse_tool_calls()."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    body_dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tool_choice": "none",
    }
    if seed is not None:
        body_dict["seed"] = seed
    body = json.dumps(body_dict).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=4000) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    msg = data["choices"][0]["message"]
    return _detokenize_bpe((msg.get("reasoning") or "") + (msg.get("content") or ""))


# ----- Main loop -----

SYSTEM_PROMPT = """You are an expert Python engineer competing in reward-bench Tier 1 — the 2048 FSM-solver task.

You have read access to the task spec and the env source, and write access to /workspace.

Tool calls go in fenced code blocks tagged `tool` with a JSON body. One or more per turn. Examples:

```tool
{"name": "view", "args": {"path": "/tasks/2048/SKILL_tier1.md"}}
```
  Read a file (paths must start with /workspace, /env, or /tasks).

```tool
{"name": "write_file", "args": {"path": "/workspace/submission.py"}}
===FILE_BODY===
from __future__ import annotations
import math
... your full file, raw, no JSON escaping ...
```
  Overwrite a file under /workspace. Inside the SAME ```tool block, after a
  line containing exactly `===FILE_BODY===`, put the file content as raw
  text. NO JSON escaping — newlines, quotes, backslashes all literal. The
  `===FILE_BODY===` separator is REQUIRED to start the content region.
  Everything between that line and the closing ``` becomes the file body.
  IMPORTANT: do NOT use `===FILE_BODY===` anywhere inside the file body
  itself — it's a parser separator, not a section marker.

```tool
{"name": "bash", "args": {"cmd": "python3 /tasks/2048/dev_runner.py /workspace/submission.py"}}
```
  Run an allow-listed command. The dev_runner gives you fast feedback (5
  dev-seed games, ~1-5 s total). Use python3 — `python` is not available.

```tool
{"name": "finish", "args": {"note": "why you're done"}}
```
  Stop. Whatever is at /workspace/submission.py at finish time gets scored.

You are in a ralph loop: write → bash dev_runner → observe → refine → repeat
until finished or budget exhausted. Be deliberate — quality matters more than
turn count. READ THE SKILL SPEC FIRST so you understand the FSM contract,
allowed imports, and anti-cheat rules.

Always emit at least one tool call per turn. If you're done, emit a `finish`
tool call rather than free text — only `finish` stops the loop. WHEN TO
FINISH: as soon as your dev_runner mean stops improving for two consecutive
iterations, your previous-best submission is what scores. Whatever is at
/workspace/submission.py at finish time is what gets scored — make sure it
is your best version, not the latest experimental one."""

FIRST_USER = """Start the task. Read /tasks/2048/SKILL_tier1.md to learn the constraints, then optionally /env/env_2048.py for env details, then write your submission to /workspace/submission.py and iterate. Use the fenced-block JSON tool format the system prompt described."""


_DEV_MEAN_RE = re.compile(r"^\s*MEAN=(\d+)\b", re.MULTILINE)


def _parse_dev_mean(bash_obs: str) -> int | None:
    """Parse dev_runner output bash observation for MEAN=N. None if not found."""
    m = _DEV_MEAN_RE.search(bash_obs)
    return int(m.group(1)) if m else None


def _snapshot_best(workspace: "Path") -> bool:
    """Copy submission.py → submission.best.py. Returns True on success."""
    src = workspace / "submission.py"
    dst = workspace / "submission.best.py"
    if not src.exists():
        return False
    try:
        dst.write_bytes(src.read_bytes())
        return True
    except Exception:
        return False


def _restore_best(workspace: "Path") -> bool:
    """Copy submission.best.py → submission.py at end of loop, if best exists."""
    src = workspace / "submission.best.py"
    dst = workspace / "submission.py"
    if not src.exists():
        return False
    try:
        dst.write_bytes(src.read_bytes())
        return True
    except Exception:
        return False


def _summarize_messages(msgs: list[dict], condenser_shim: str,
                        condenser_model: str, condenser_api_key: str) -> str:
    """Send msgs to condenser LLM, get back a concise summary string."""
    transcript = "\n\n".join(
        f"[{m['role']}]\n{m.get('content', '') or m.get('reasoning', '') or ''}" for m in msgs
    )
    prompt = (
        "You are a context condenser. Summarize the following conversation between an "
        "agent and its tool environment. Preserve: (1) the user's task and constraints; "
        "(2) what the agent has already tried; (3) what the agent has discovered or "
        "decided; (4) the current state of /workspace/submission.py and any dev_runner "
        "scores observed; (5) the agent's plan for the next steps. Be concise but "
        "complete. Output the summary only, no preamble.\n\n"
        + transcript
    )
    body = json.dumps({
        "model": condenser_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 4096,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{condenser_shim.rstrip('/')}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {condenser_api_key}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    msg = data["choices"][0]["message"]
    return _detokenize_bpe((msg.get("reasoning") or "") + (msg.get("content") or ""))


def _condense_history(messages: list[dict], condenser_args) -> list[dict]:
    """Replace middle turns with a single LLM-generated summary message.

    Keeps: messages[0] (system), messages[1] (first user), messages[-2*keep_recent:]
    (last N turn-pairs).
    """
    keep = condenser_args.condenser_keep_recent
    head = messages[:2]
    tail_n = max(2, 2 * keep)
    tail = messages[-tail_n:] if len(messages) > 2 + tail_n else []
    middle = messages[2:-tail_n] if tail else messages[2:]
    if not middle:
        return messages

    summary_text = _summarize_messages(
        middle,
        condenser_args.condenser_shim,
        condenser_args.condenser_model,
        condenser_args.condenser_api_key,
    )
    summary_msg = {
        "role": "user",
        "content": (
            "[CONDENSED HISTORY — earlier turns summarized by condenser model]\n\n"
            + summary_text
            + "\n\n[END CONDENSED HISTORY — recent turns continue below]"
        ),
    }
    return head + [summary_msg] + tail


def _get_max_model_len(shim_url: str, api_key: str, model: str) -> int | None:
    """GET shim/v1/models. Return max_model_len for `model`, or None if unknown."""
    try:
        url = f"{shim_url.rstrip('/')}/models"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for entry in data.get("data", []):
            if entry.get("id") == model and entry.get("max_model_len"):
                return int(entry["max_model_len"])
        # Fallback: first entry's max_model_len if there's only one.
        entries = data.get("data", [])
        if len(entries) == 1 and entries[0].get("max_model_len"):
            return int(entries[0]["max_model_len"])
    except Exception:
        return None
    return None


def _check_context_guardrail(args) -> None:
    """Refuse to start if the budget would exceed vLLM's reject threshold.

    vLLM rejects requests where prompt_tokens + max_tokens > max_model_len.
    Our effective input ceiling is therefore max_model_len - 12288 (call_llm's
    default max_tokens). If --condenser-trigger-tokens (when condenser is
    enabled) or --context-budget-tokens (when not) >= that ceiling, the
    watchdog/condenser fires too late and the loop hits an HTTP 400 cascade.
    """
    max_model_len = _get_max_model_len(args.shim, args.api_key, args.model)
    if max_model_len is None:
        print("[guardrail] could not read max_model_len from shim — skipping check", flush=True)
        return
    # 12288 is call_llm's default max_tokens per request. Mirrored here.
    max_safe_input = max_model_len - 12288
    condenser_enabled = bool(args.condenser_shim and args.condenser_model)

    if condenser_enabled:
        knob = "--condenser-trigger-tokens"
        val = args.condenser_trigger_tokens
    else:
        knob = "--context-budget-tokens"
        val = args.context_budget_tokens

    if val >= max_safe_input:
        sys.stderr.write(
            "[guardrail] context budget would exceed max_safe_input.\n"
            f"  candidate max_model_len = {max_model_len}\n"
            f"  max_tokens reserved per call = 12288\n"
            f"  max_safe_input = {max_safe_input} (= max_model_len - max_tokens)\n"
            f"  {knob} = {val}  (must be < max_safe_input)\n"
            "Lower the value, raise the candidate's max_model_len, or run without\n"
            "this guardrail by editing _check_context_guardrail.\n"
        )
        sys.exit(2)
    print(f"[guardrail] OK: {knob}={val} < max_safe_input={max_safe_input} "
          f"(max_model_len={max_model_len})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shim", required=True, help="OpenAI-compatible base URL, e.g. http://localhost:8765/v1")
    ap.add_argument("--api-key", default="fixture")
    ap.add_argument("--model", default="claude-fixture")
    ap.add_argument("--workspace", required=True, help="rw scratch + final submission.py lives here")
    ap.add_argument("--tasks-dir", required=True, help="ro mount with task files")
    ap.add_argument("--env-dir", required=True, help="ro mount with env_2048.py")
    ap.add_argument("--max-iters", type=int, default=30, help="hard cap on agent turns (default: 30 — placed-model trajectories show peak by 60-80%)")
    ap.add_argument("--max-no-improve", type=int, default=5,
                    help="stop loop after N consecutive dev_runs without improving best dev MEAN (default: 5)")
    ap.add_argument("--finish-floor", type=int, default=7211,
                    help="reject `finish` if best dev MEAN < this (default: 7211 = reference_fsm.py mean)")
    ap.add_argument("--seed", type=int, default=None,
                    help="seed for sampling (passed to /v1/chat/completions seed param). None = no seed.")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="sampling temperature (default: 0.0 = greedy/deterministic). For multi-seed variance, use 0.7-1.0.")
    ap.add_argument("--condenser-shim", default=None,
                    help="OpenAI-compat URL for the condenser model. If set with --condenser-model, history >--condenser-trigger-tokens is summarized via this endpoint.")
    ap.add_argument("--condenser-model", default=None,
                    help="model name on the condenser shim (e.g., qwen2.5-7b-nvfp4).")
    ap.add_argument("--condenser-api-key", default="fixture",
                    help="API key for condenser shim (default: fixture).")
    ap.add_argument("--condenser-trigger-tokens", type=int, default=80_000,
                    help="trigger condensation when approx token count exceeds this (default: 80k).")
    ap.add_argument("--condenser-keep-recent", type=int, default=8,
                    help="condense everything except the system, first user, and last N turn-pairs (default: 8).")
    ap.add_argument("--max-wall-sec", type=float, default=7200.0, help="hard cap on wall time, runaway protection only (default: 2 h)")
    ap.add_argument("--context-budget-tokens", type=int, default=200_000,
                    help="approx token budget for conversation; older turns are pruned past this (default: 200k of the 256k qwen3.6 window)")
    ap.add_argument("--trace", default=None, help="optional path to write events.jsonl trace")
    args = ap.parse_args()
    _check_context_guardrail(args)

    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    tasks_dir = Path(args.tasks_dir).resolve()
    env_dir = Path(args.env_dir).resolve()

    trace_fp = open(args.trace, "w") if args.trace else None
    def trace(event: dict):
        event["t"] = time.time()
        if trace_fp:
            trace_fp.write(json.dumps(event, ensure_ascii=False) + "\n")
            trace_fp.flush()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": FIRST_USER},
    ]

    t0 = time.time()
    finished = False
    best_dev_mean = -1
    no_improve_count = 0
    plateau_stopped = False
    iter_n = 0

    while iter_n < args.max_iters and (time.time() - t0) < args.max_wall_sec and not finished:
        iter_n += 1
        print(f"\n=== turn {iter_n} ===", flush=True)
        trace({"event": "turn_start", "iter": iter_n})

        # Context-length watchdog — prune older turns when projected token
        # count exceeds the budget. Keeps system prompt + first user + most
        # recent turns intact, drops oldest middle turns.
        approx = _approx_tokens(messages)
        condenser_enabled = args.condenser_shim and args.condenser_model
        condenser_threshold = args.condenser_trigger_tokens if condenser_enabled else args.context_budget_tokens
        if approx > condenser_threshold:
            n_before = len(messages)
            if condenser_enabled:
                try:
                    messages = _condense_history(messages, args)
                    trace({"event": "history_condensed", "before_msgs": n_before,
                           "after_msgs": len(messages),
                           "before_approx_tokens": approx,
                           "after_approx_tokens": _approx_tokens(messages),
                           "condenser_model": args.condenser_model})
                    print(f"[watchdog] condensed history {n_before}→{len(messages)} msgs, "
                          f"~{approx} → ~{_approx_tokens(messages)} tokens via "
                          f"{args.condenser_model}", flush=True)
                except Exception as e:
                    print(f"[watchdog] condenser call failed ({e}); falling back to prune", flush=True)
                    messages = _prune_history(messages, args.context_budget_tokens)
                    trace({"event": "history_pruned_fallback", "err": str(e),
                           "before_msgs": n_before, "after_msgs": len(messages)})
            else:
                messages = _prune_history(messages, args.context_budget_tokens)
                trace({"event": "history_pruned", "before_msgs": n_before,
                       "after_msgs": len(messages),
                       "before_approx_tokens": approx,
                       "after_approx_tokens": _approx_tokens(messages)})
                print(f"[watchdog] pruned history {n_before}→{len(messages)} msgs, "
                      f"~{approx} → ~{_approx_tokens(messages)} tokens", flush=True)

        try:
            reply = call_llm(args.shim, args.api_key, args.model, messages,
                             temperature=args.temperature, seed=args.seed)
        except Exception as e:
            err = f"<error>llm call failed: {e}</error>"
            print(err)
            trace({"event": "llm_error", "err": str(e)})
            messages.append({"role": "user", "content": err})
            continue

        print(f"--- reply ---\n{_trim(reply, 2000)}", flush=True)
        trace({"event": "llm_reply", "reply_len": len(reply)})
        messages.append({"role": "assistant", "content": reply})

        tool_calls = parse_tool_calls(reply)
        if not tool_calls:
            obs = ("<error>no tool calls found in your reply. Each tool call must be in a "
                   "fenced code block tagged `tool` containing JSON like "
                   "```tool\\n{\"name\": \"view\", \"args\": {\"path\": \"/...\"}}\\n```. "
                   "Allowed names: view, write_file, bash, finish.</error>")
            print(obs, flush=True)
            messages.append({"role": "user", "content": obs})
            trace({"event": "no_tool_calls"})
            continue

        observations: list[str] = []
        for name, tool_args in tool_calls:
            obs = execute_tool(name, tool_args, workspace, env_dir, tasks_dir)
            print(f"--- tool {name} ---\n{_trim(obs, 2000)}", flush=True)
            trace({"event": "tool_call", "name": name, "args_keys": list(tool_args.keys())})

            # --- best-checkpoint + plateau detection on dev_runner bash output ---
            if name == "bash":
                dev_mean = _parse_dev_mean(obs)
                if dev_mean is not None:
                    if dev_mean > best_dev_mean:
                        best_dev_mean = dev_mean
                        no_improve_count = 0
                        snapped = _snapshot_best(workspace)
                        print(f"[harness] new best dev MEAN={dev_mean} (snapshot={snapped})", flush=True)
                        trace({"event": "best_snapshot", "dev_mean": dev_mean,
                               "iter": iter_n})
                    else:
                        no_improve_count += 1
                        print(f"[harness] no-improve {no_improve_count}/{args.max_no_improve} (this={dev_mean}, best={best_dev_mean})", flush=True)
                        trace({"event": "no_improve", "dev_mean": dev_mean,
                               "best": best_dev_mean, "count": no_improve_count})
                    if no_improve_count >= args.max_no_improve:
                        plateau_stopped = True
                        print(f"[harness] plateau-stop after {args.max_no_improve} non-improving dev_runs", flush=True)
                        trace({"event": "plateau_stop", "best_dev_mean": best_dev_mean,
                               "iter": iter_n})

            # --- finish-floor: reject finish() below the reference_fsm.py baseline ---
            if name == "finish":
                if best_dev_mean < args.finish_floor:
                    rejected = (
                        f"<error>finish rejected: best dev MEAN so far is "
                        f"{best_dev_mean if best_dev_mean >= 0 else 'unknown (no dev_run yet)'}, "
                        f"which is below the reference_fsm.py baseline ({args.finish_floor}). "
                        f"You must produce a submission scoring above this floor before finishing. "
                        f"Run `python /tasks/2048/dev_runner.py /workspace/submission.py` to test, "
                        f"then refine your FSM until dev MEAN exceeds {args.finish_floor}.</error>"
                    )
                    obs = rejected
                    print(f"[harness] finish rejected (best_dev_mean={best_dev_mean} < floor={args.finish_floor})", flush=True)
                    trace({"event": "finish_rejected", "best_dev_mean": best_dev_mean,
                           "floor": args.finish_floor})
                else:
                    finished = True

            observations.append(obs)

        messages.append({"role": "user", "content": "\n\n".join(observations)})

        if plateau_stopped:
            break

    elapsed = time.time() - t0
    submission = workspace / "submission.py"
    best_path = workspace / "submission.best.py"
    restored = False
    if best_path.exists():
        restored = _restore_best(workspace)
        if restored:
            print(f"[harness] restored submission.best.py (dev MEAN={best_dev_mean}) to submission.py for Stage 2", flush=True)
            trace({"event": "best_restored", "dev_mean": best_dev_mean})
    summary = {
        "iterations": iter_n,
        "wall_sec": elapsed,
        "finished_via_tool": finished,
        "plateau_stopped": plateau_stopped,
        "best_dev_mean": best_dev_mean,
        "best_restored": restored,
        "submission_exists": submission.exists(),
        "submission_size": submission.stat().st_size if submission.exists() else 0,
    }
    print(f"\n=== agent loop done ===\n{json.dumps(summary, indent=2)}")
    trace({"event": "done", **summary})
    if trace_fp:
        trace_fp.close()
    return 0 if submission.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
