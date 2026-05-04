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


def execute_tool(name: str, args: dict[str, str], workspace: Path, env_dir: Path, tasks_dir: Path) -> str:
    """Run one tool. Returns observation text the model will see next turn."""
    if name == "view":
        path = Path(args.get("path", "")).resolve()
        # Restrict reads to the three mounts
        allowed_roots = [workspace.resolve(), env_dir.resolve(), tasks_dir.resolve()]
        if not any(str(path).startswith(str(root)) for root in allowed_roots):
            return f"<error>view: path outside allowed roots ({path})</error>"
        if not path.exists():
            return f"<error>view: file not found: {path}</error>"
        try:
            return f"<view path=\"{path}\">\n{_trim(path.read_text())}\n</view>"
        except Exception as e:
            return f"<error>view: {e}</error>"

    if name == "write_file":
        path = Path(args.get("path", ""))
        content = args.get("content", "")
        if not str(path.resolve()).startswith(str(workspace.resolve())):
            return f"<error>write_file: writes only allowed under /workspace ({path})</error>"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"<ok>wrote {len(content)} chars to {path}</ok>"

    if name == "bash":
        cmd = args.get("cmd", "").strip()
        if not any(cmd.startswith(p) for p in ALLOWED_BASH_PREFIXES):
            return f"<error>bash: command not on allow-list. Allowed prefixes:\n" + "\n".join(f"  {p}" for p in ALLOWED_BASH_PREFIXES) + f"\nReceived: {cmd}</error>"
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=120,
                cwd=str(workspace),
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

# Match <tool name="X"> ... </tool>, capturing name + body.
_TOOL_RE = re.compile(r"<tool\s+name=\"([^\"]+)\"\s*>(.*?)</tool>", re.DOTALL)
# Match <key>value</key> inside the body.
_ARG_RE = re.compile(r"<([a-z_]+)>(.*?)</\1>", re.DOTALL)


def parse_tool_calls(text: str) -> list[tuple[str, dict[str, str]]]:
    out: list[tuple[str, dict[str, str]]] = []
    for m in _TOOL_RE.finditer(text):
        name = m.group(1).strip()
        body = m.group(2)
        args: dict[str, str] = {}
        for am in _ARG_RE.finditer(body):
            args[am.group(1)] = am.group(2)
        out.append((name, args))
    return out


# ----- LLM client -----

def call_llm(base_url: str, api_key: str, model: str, messages: list[dict], temperature: float = 0.0) -> str:
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
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
    return data["choices"][0]["message"]["content"]


# ----- Main loop -----

SYSTEM_PROMPT = """You are an expert Python engineer competing in reward-bench Tier 1 — the 2048 FSM-solver task.

You have read access to the task spec and the env source, and write access to /workspace.

Available tools (use these exact XML tags; one or more per turn):

  <tool name="view"><path>/path</path></tool>
      Read a file (limited to /workspace, /env, /tasks).

  <tool name="write_file"><path>/workspace/submission.py</path><content>
  ...your code...
  </content></tool>
      Overwrite a file under /workspace.

  <tool name="bash"><cmd>python /tasks/2048/dev_runner.py /workspace/submission.py</cmd></tool>
      Run an allow-listed command. The dev_runner gives you fast feedback
      (5 dev-seed games, ~1 sec total).

  <tool name="finish"><note>why you're done</note></tool>
      Stop. Whatever's at /workspace/submission.py gets scored.

You are in a ralph loop: write → bash dev_runner → observe → refine → repeat until finished or budget exhausted. Be deliberate; quality matters more than turn count. Read the SKILL spec FIRST."""

FIRST_USER = """Start the task. Read /tasks/2048/SKILL_tier1.md to learn the constraints, then optionally /env/env_2048.py for env details, then write your submission to /workspace/submission.py and iterate."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shim", required=True, help="OpenAI-compatible base URL, e.g. http://localhost:8765/v1")
    ap.add_argument("--api-key", default="fixture")
    ap.add_argument("--model", default="claude-fixture")
    ap.add_argument("--workspace", required=True, help="rw scratch + final submission.py lives here")
    ap.add_argument("--tasks-dir", required=True, help="ro mount with task files")
    ap.add_argument("--env-dir", required=True, help="ro mount with env_2048.py")
    ap.add_argument("--max-iters", type=int, default=20, help="hard cap on agent turns")
    ap.add_argument("--max-wall-sec", type=float, default=3600.0, help="hard cap on wall time")
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
            obs = "<error>no tool calls found in your reply. You must use one of: view, write_file, bash, finish. Wrap each call in <tool name=\"X\">...</tool>.</error>"
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
