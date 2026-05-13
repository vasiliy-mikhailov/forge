"""Tier 1 interactive agent loop. See src-spec/tier1/.

Per SPEC.md Submission Protocols, the interactive protocol is the
currently-implemented mode. Lifted verbatim from _bak/bin/agent_loop.py
(May 2026 production campaign, ~15.9k mean score on Qwen3.6-27B-AWQ).
"""
import json
import re
from pathlib import Path


_TOOL_BLOCK_RE = re.compile(r'```tool\b\s*\n(.*?)\n```', re.DOTALL)


def parse_tool_calls(reply):
    out = []
    for m in _TOOL_BLOCK_RE.finditer(reply):
        body = m.group(1).strip()
        obj = json.loads(body)
        out.append((obj['name'], obj['args']))
    return out


def _trim(s, n=4000):
    if len(s) <= n:
        return s
    return s[: n - 200] + f"\n... [truncated, total {len(s)} chars]"


def _virt_to_host(virt, workspace, env_dir, tasks_dir):
    """Resolve a model-supplied virtual path to a host path. Returns None if
    the path doesn't sit under one of the allowed virtual roots."""
    if not virt:
        return None
    p = virt.strip()
    while '//' in p:
        p = p.replace('//', '/')
    for prefix, root in (('/workspace', workspace), ('/env', env_dir), ('/tasks', tasks_dir)):
        if p == prefix or p.startswith(prefix + '/'):
            tail = p[len(prefix):].lstrip('/')
            host = (Path(root) / tail).resolve() if tail else Path(root).resolve()
            # Defence-in-depth: post-resolve check to block ../ escapes
            if not str(host).startswith(str(Path(root).resolve())):
                return None
            return host
    return None


def execute_tool(name, args, workspace, env_dir, tasks_dir):
    """Run one tool. Returns observation text the model will see next turn."""
    if name == 'view':
        virt = args.get('path', '')
        host = _virt_to_host(virt, workspace, env_dir, tasks_dir)
        if host is None:
            return f'<error>view: path must start with /workspace, /env, or /tasks (got {virt!r})</error>'
        if not host.exists():
            return f'<error>view: file not found: {virt}</error>'
        try:
            return f'<view path="{virt}">\n{_trim(host.read_text())}\n</view>'
        except Exception as e:
            return f'<error>view: {e}</error>'

    if name == 'write_file':
        virt = args.get('path', '')
        content = args.get('content', '')
        host = _virt_to_host(virt, workspace, env_dir, tasks_dir)
        if host is None:
            return f'<error>write_file: path must start with /workspace (got {virt!r})</error>'
        if not str(host).startswith(str(Path(workspace).resolve())):
            return f'<error>write_file: writes only allowed under /workspace (got {virt!r})</error>'
        host.parent.mkdir(parents=True, exist_ok=True)
        host.write_text(content)
        return f'<ok>wrote {len(content)} chars to {virt}</ok>'

    return f'<error>unknown tool: {name}</error>'


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
