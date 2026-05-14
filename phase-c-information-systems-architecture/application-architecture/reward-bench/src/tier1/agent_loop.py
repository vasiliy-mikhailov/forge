"""Tier 1 interactive agent loop. See src-spec/tier1/.

Per SPEC.md Submission Protocols, the interactive protocol is the
currently-implemented mode. Lifted verbatim from _bak/bin/agent_loop.py
(May 2026 production campaign, ~15.9k mean score on Qwen3.6-27B-AWQ).
"""
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path


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


_TOOL_BLOCK_RE = re.compile(r'```tool\b\s*\n(.*?)\n```', re.DOTALL)
_BODY_SPLIT_RE = re.compile(r'\n===FILE_BODY===\s*\n', re.DOTALL)


def parse_tool_calls(reply):
    out = []
    for m in _TOOL_BLOCK_RE.finditer(reply):
        raw = m.group(1)
        parts = _BODY_SPLIT_RE.split(raw, maxsplit=1)
        json_part = parts[0].strip()
        body_part = parts[1] if len(parts) == 2 else None
        obj = json.loads(json_part)
        name = obj['name']
        args = dict(obj.get('args') or {})
        if body_part is not None:
            args['content'] = body_part
        out.append((name, args))
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

    if name == 'bash':
        virt_cmd = args.get('cmd', '').strip()
        if not any(virt_cmd.startswith(p) for p in ALLOWED_BASH_PREFIXES):
            return ('<error>bash: command not on allow-list. Allowed prefixes:\n'
                    + '\n'.join(f'  {p}' for p in ALLOWED_BASH_PREFIXES)
                    + f'\nReceived: {virt_cmd}</error>')
        cmd = virt_cmd
        for prefix, root in (('/workspace', workspace), ('/tasks', tasks_dir), ('/env', env_dir)):
            cmd = cmd.replace(prefix, str(Path(root).resolve()))
        env = os.environ.copy()
        env['PYTHONPATH'] = f"{Path(env_dir).resolve()}:" + env.get('PYTHONPATH', '')
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=120,
                cwd=str(workspace), env=env,
            )
            stdout = _trim(result.stdout)
            stderr = _trim(result.stderr)
            return (f'<bash exit={result.returncode}>\n'
                    f'--- stdout ---\n{stdout}\n'
                    f'--- stderr ---\n{stderr}\n'
                    f'</bash>')
        except subprocess.TimeoutExpired:
            return '<error>bash: timed out after 120s</error>'
        except Exception as e:
            return f'<error>bash: {e}</error>'

    if name == 'finish':
        note = args.get('note', '')
        return f'<finish>{note}</finish>'

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


FIRST_USER = """Start the task.

REQUIRED API CONTRACT (do NOT deviate; the harness loads your submission
exactly this way):

    # /workspace/submission.py
    from transitions import Machine

    class Solver:                    # <-- exact name `Solver`, capital S
        def __init__(self):
            # build your state machine with `transitions` here
            ...

        def move(self, board: list[list[int]]) -> str:
            # board is a 4x4 list of ints (0 = empty; tiles are powers of 2)
            # return EXACTLY ONE of the four characters: 'W', 'A', 'S', 'D'
            # (W=up, A=left, S=down, D=right)
            ...

Common mistakes to avoid:
  - DO NOT write `def solve(state)` returning ints 0/1/2/3 — wrong shape.
  - DO NOT return strings like 'up'/'down' — must be 'W'/'A'/'S'/'D'.
  - DO NOT skip the `transitions` library — the spec mandates an FSM
    declared with `transitions.Machine`.

Workflow:
  1. View /tasks/2048/SKILL_tier1.md for the full task spec.
  2. (optional) View /env/env_2048.py for the env API.
  3. Write /workspace/submission.py respecting the API contract above.
  4. Run `bash python3 /tasks/2048/dev_runner.py /workspace/submission.py`
     BEFORE calling finish. The dev_runner will error loudly if your
     Solver class is missing or move() returns the wrong type — fix
     and retry. Only call finish once dev_runner prints non-zero scores
     for every seed.

Use the fenced-block JSON tool format the system prompt described."""


def _call_model(vllm_base_url, vllm_api_key, messages, max_tokens=32768, temperature=0.0):
    payload = json.dumps({
        'model': 'qwen3.6-27b-awq',
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode()
    req = urllib.request.Request(
        f'{vllm_base_url}/v1/chat/completions',
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {vllm_api_key}',
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.loads(r.read())
    return data['choices'][0]['message']['content']


def _identity_condense(messages):
    """Default condense: pass messages through unchanged."""
    return tuple(messages)


def run_loop(workspace, env_dir, tasks_dir, vllm_base_url, vllm_api_key,
             max_iters, condense=_identity_condense, temperature=0.0,
             supervisor=None, supervisor_every_k=0):
    """Drive the interactive agent loop for at most max_iters turns.

    `condense` is an opaque callable that takes the message tuple and
    returns a (possibly shorter) tuple. Called BEFORE every _call_model
    invocation. Default is identity. See
    src-spec/tier1/agent_loop/src_spec_when_run_loop_called_with_condense_callable_*
    for the seam contract; see reward-bench/docs/adr/0001 for the
    same-model decision used by the concrete LlmCondenser adapter.

    `temperature` is the Stage-1 author-loop sampling temperature
    passed through to `_call_model`. Default 0.0 (deterministic) for
    test isolation; the bench orchestrator (`main()`) passes
    `BenchConfig.temperature` per ADR 0003 (0.7 for exploration).

    `supervisor` (cycle 33, ADR 0005): optional SupervisorPort impl
    consulted every `supervisor_every_k` iterations to judge whether
    the agent has plateaued. When the supervisor returns
    `stop_recommended=True`, the loop terminates early with
    `finished=True` and a synthetic note carrying the supervisor's
    reasoning.

    `supervisor_every_k` (cycle 33): consult cadence. Default 0 means
    NEVER consult (cycle-12 behavior; no change for existing campaigns
    that pass no supervisor or pass NullSupervisor).

    Returns {iterations, messages, finished}.
    """
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': FIRST_USER},
    ]
    finished = False
    iter_n = 0
    while iter_n < max_iters and not finished:
        iter_n += 1
        messages = list(condense(tuple(messages)))
        reply = _call_model(vllm_base_url, vllm_api_key, messages,
                            temperature=temperature)
        messages.append({'role': 'assistant', 'content': reply})
        tool_calls = parse_tool_calls(reply)
        if not tool_calls:
            obs = ('<error>no tool calls found in your reply. Each tool call '
                   'must be in a fenced code block tagged `tool`.</error>')
            messages.append({'role': 'user', 'content': obs})
            continue
        observations = []
        for name, tool_args in tool_calls:
            obs = execute_tool(name, tool_args, workspace, env_dir, tasks_dir)
            observations.append(obs)
            if name == 'finish':
                finished = True
        messages.append({'role': 'user', 'content': '\n\n'.join(observations)})
        # Cycle 33 (ADR 0005): supervisor hook. Every K iters, ask the
        # supervisor whether to stop. We feed it a minimal per-iter sample
        # `(iter_n, 0.0, 0, 0.0)` for now — cycle 34 will parse real
        # dev_runner output into mean_score / max_tile.
        if (supervisor is not None
                and supervisor_every_k > 0
                and iter_n % supervisor_every_k == 0
                and not finished):
            sweep = tuple((i, 0.0, 0, 0.0) for i in range(1, iter_n + 1))
            decision = supervisor.judge(sweep)
            if decision.stop_recommended:
                messages.append({
                    'role': 'user',
                    'content': (
                        f'<supervisor>stop_recommended=True. '
                        f'reasoning: {decision.reasoning}</supervisor>'
                    ),
                })
                finished = True
    return {'iterations': iter_n, 'messages': messages, 'finished': finished}
