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

_TOOL_BLOCK_RE = re.compile(r"```tool\s*\n(.*?)\n```", re.DOTALL)
# Fallback: an unclosed ```tool block at the end of the reply. Some models
# (notably Qwen 3.6) hit a practical generation cap around ~9 KB and stop
# emitting tokens before they reach the closing fence. This still gives us
# a parseable tool call most of the time — better than dropping the turn.
_TOOL_BLOCK_TRAILING_RE = re.compile(r"```tool\s*\n(.*)\Z", re.DOTALL)
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
             temperature: float = 0.0, max_tokens: int = 12288) -> str:
    """POST to an OpenAI-compat /v1/chat/completions endpoint.

    max_tokens is set explicitly because some servers (incl. vLLM with default
    config) cap completions at a small number that truncates tool calls
    mid-tag.

    tool_choice="none" disables vLLM's auto-tool-choice parser, which
    otherwise intercepts our XML-style <tool name="…"> blocks (Qwen's tool
    parser collides with our convention). We do our own parsing in
    parse_tool_calls()."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tool_choice": "none",
    }).encode("utf-8")
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
    return (msg.get("reasoning") or "") + (msg.get("content") or "")


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shim", required=True, help="OpenAI-compatible base URL, e.g. http://localhost:8765/v1")
    ap.add_argument("--api-key", default="fixture")
    ap.add_argument("--model", default="claude-fixture")
    ap.add_argument("--workspace", required=True, help="rw scratch + final submission.py lives here")
    ap.add_argument("--tasks-dir", required=True, help="ro mount with task files")
    ap.add_argument("--env-dir", required=True, help="ro mount with env_2048.py")
    ap.add_argument("--max-iters", type=int, default=100, help="hard cap on agent turns (default: 100)")
    ap.add_argument("--max-wall-sec", type=float, default=7200.0, help="hard cap on wall time, runaway protection only (default: 2 h)")
    ap.add_argument("--context-budget-tokens", type=int, default=200_000,
                    help="approx token budget for conversation; older turns are pruned past this (default: 200k of the 256k qwen3.6 window)")
    ap.add_argument("--trace", default=None, help="optional path to write events.jsonl trace")
    args = ap.parse_args()

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
    iter_n = 0

    while iter_n < args.max_iters and (time.time() - t0) < args.max_wall_sec and not finished:
        iter_n += 1
        print(f"\n=== turn {iter_n} ===", flush=True)
        trace({"event": "turn_start", "iter": iter_n})

        # Context-length watchdog — prune older turns when projected token
        # count exceeds the budget. Keeps system prompt + first user + most
        # recent turns intact, drops oldest middle turns.
        approx = _approx_tokens(messages)
        if approx > args.context_budget_tokens:
            n_before = len(messages)
            messages = _prune_history(messages, args.context_budget_tokens)
            trace({"event": "history_pruned", "before_msgs": n_before,
                   "after_msgs": len(messages),
                   "before_approx_tokens": approx,
                   "after_approx_tokens": _approx_tokens(messages)})
            print(f"[watchdog] pruned history {n_before}→{len(messages)} msgs, ~{approx} → ~{_approx_tokens(messages)} tokens", flush=True)

        try:
            reply = call_llm(args.shim, args.api_key, args.model, messages)
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
            observations.append(obs)
            if name == "finish":
                finished = True

        messages.append({"role": "user", "content": "\n\n".join(observations)})

    elapsed = time.time() - t0
    submission = workspace / "submission.py"
    summary = {
        "iterations": iter_n,
        "wall_sec": elapsed,
        "finished_via_tool": finished,
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
