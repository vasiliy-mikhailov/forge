"""Tier 1 interactive agent loop. See src-spec/tier1/.

Per SPEC.md Submission Protocols, the interactive protocol is the
currently-implemented mode. Lifted verbatim from _bak/bin/agent_loop.py
(May 2026 production campaign, ~15.9k mean score on Qwen3.6-27B-AWQ).
"""
import json
import os
import re
import shutil
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
    """Cycle 51 / hypothesis #9: defensive parser. Bad JSON in one block
    must not abort the iteration — return [] for that block so the loop
    treats it as 'no tool calls' and the model gets another turn."""
    out = []
    for m in _TOOL_BLOCK_RE.finditer(reply):
        raw = m.group(1)
        parts = _BODY_SPLIT_RE.split(raw, maxsplit=1)
        json_part = parts[0].strip()
        body_part = parts[1] if len(parts) == 2 else None
        try:
            obj = json.loads(json_part)
        except json.JSONDecodeError:
            # Legacy fallback: strip trailing commas/whitespace and retry.
            try:
                obj = json.loads(json_part.rstrip(', \t\n'))
            except json.JSONDecodeError:
                continue
        if not isinstance(obj, dict):
            continue
        name = str(obj.get('name', '')).strip()
        if not name:
            continue
        raw_args = obj.get('args') or {}
        if not isinstance(raw_args, dict):
            raw_args = {}
        args = dict(raw_args)
        if body_part is not None:
            args['content'] = body_part
        out.append((name, args))
    return out


def _trim(s, n=4000):
    if len(s) <= n:
        return s
    return s[: n - 200] + f"\n... [truncated, total {len(s)} chars]"


# Cycle 34: dev_runner emits a summary line shaped like
#   MEAN=5000.0  MEDIAN=4800.0  max-tile-best=512  (1.5s total)
# This regex extracts mean, max_tile, walltime to feed the supervisor
# sweep per ADR 0005. None when no match (the caller emits a zero-filled
# placeholder so n_samples == iter_count).
_DEV_RUNNER_SUMMARY_RE = re.compile(
    r"MEAN=([0-9]+(?:\.[0-9]+)?)\s+"
    r"MEDIAN=[0-9]+(?:\.[0-9]+)?\s+"
    r"max-tile-best=([0-9]+)\s+"
    r"\(([0-9]+(?:\.[0-9]+)?)s total\)"
)


def _parse_dev_runner_summary(obs_text):
    """Return (mean_score, max_tile, walltime_sec) or None.

    Cycle 34: matches the legacy bash dev_runner stdout summary line.
    Cycle 63 (ADR 0008): ALSO matches the execute_submission JSON
    observation wrapped in <observation>...</observation> so the active
    tool feeds the same best_dev_mean / supervisor sweep / finish-floor
    accumulators as the legacy path.
    """
    # Active path (ADR 0008): JSON observation.
    if "<observation>" in obs_text:
        try:
            import json as _json
            start = obs_text.index("<observation>") + len("<observation>")
            end = obs_text.index("</observation>", start)
            payload = _json.loads(obs_text[start:end])
            if not isinstance(payload, dict):
                pass
            elif payload.get("per_seed"):
                mean = float(payload.get("mean", 0.0))
                max_tile = int(payload.get("max_tile_best", 0))
                walltime = float(payload.get("walltime_sec_total", 0.0))
                return (mean, max_tile, walltime)
            # Empty per_seed (protocol violation / SyntaxError) => no parse.
        except (ValueError, KeyError):
            pass
    # Legacy path: bash dev_runner stdout regex.
    m = _DEV_RUNNER_SUMMARY_RE.search(obs_text)
    if m is None:
        return None
    return (float(m.group(1)), int(m.group(2)), float(m.group(3)))



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

    if name == 'execute_submission':
        # Cycle 58 / ADR 0008: ralph-loop atomic primitive. Model emits the
        # full submission body inline; we score on dev seeds (1..5) and
        # return a structured JSON observation. Docker isolation per ADR
        # 0006 layer 2 is a future cycle; this implementation is host-side.
        body = args.get('content', '')
        return _execute_submission(body, workspace, tasks_dir)

    return f'<error>unknown tool: {name}</error>'


_DEV_SEEDS = (1, 2, 3, 4, 5)

# Cycle 70: aggregate wall-time cap for the dev feedback path. Passed
# through to score_submission's hard_wall_sec; per-game cap derives
# from remaining budget (cycle 27 daemon-thread timeout). Without this,
# a slow Solver (e.g. cycle 69's expectimax(depth=4) with deepcopy)
# wedges the ralph loop. Monkeypatched small in tests.
DEV_HARD_WALL_S = 30.0


def _execute_submission(body, workspace, tasks_dir):
    """ADR 0008 dispatcher. Always returns a JSON-string observation;
    NEVER raises (failures land in protocol_violations / per_seed errors)."""
    import json as _json
    import sys as _sys
    import time as _t
    import importlib.util as _ilu
    obs = {
        'protocol_violations': [],
        'per_seed': [],
        'mean': 0.0,
        'median': 0,
        'max_tile_best': 0,
        'walltime_sec_total': 0.0,
    }
    sub_path = Path(workspace) / 'submission.py'
    try:
        sub_path.write_text(body)
    except Exception as e:
        obs['protocol_violations'].append(f'write failed: {type(e).__name__}: {e}')
        return '<observation>' + _json.dumps(obs) + '</observation>'

    # Load + validate protocol.
    try:
        spec = _ilu.spec_from_file_location('execute_submission_module', str(sub_path))
        module = _ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
    except SyntaxError as e:
        obs['protocol_violations'].append(f'SyntaxError: {e}')
        return '<observation>' + _json.dumps(obs) + '</observation>'
    except Exception as e:
        obs['protocol_violations'].append(f'load failed: {type(e).__name__}: {e}')
        return '<observation>' + _json.dumps(obs) + '</observation>'

    from src.tier1.harness import validate_submission_protocol
    violations = validate_submission_protocol(module)
    if violations:
        obs['protocol_violations'].extend(violations)
        return '<observation>' + _json.dumps(obs) + '</observation>'

    # Cycle 70: delegate per-game scoring to the canonical scorer. The
    # cycle-58 inline game loop is gone — the dev feedback path now
    # inherits the cycle 23/27 hard_wall_sec + per-game daemon-thread
    # timeout and the cycle 28/29 solver-error sentinels. Fixes cycle
    # 69's wedge (model wrote expectimax depth=4 → inline loop ground
    # for hours; canonical scorer sentinels under DEV_HARD_WALL_S).
    from src.tier1.use_cases.score_submission import score_submission
    from src.tier1.adapters.game_board_2048 import GameBoard2048Adapter
    try:
        _attempt = score_submission(
            solver_factory=module.Solver,
            seeds=_DEV_SEEDS,
            env=GameBoard2048Adapter(),
            hard_wall_sec=DEV_HARD_WALL_S,
        )
    except Exception as e:  # defence-in-depth: dispatcher must never raise
        obs['protocol_violations'].append(
            f'score_submission failed: {type(e).__name__}: {e}'
        )
        return '<observation>' + _json.dumps(obs) + '</observation>'

    # Thin AttemptResult -> observation transform. Preserves the cycle-63
    # parser contract (mean/median/per_seed/max_tile_best/walltime_sec_total).
    per_seed = []
    for _g in _attempt.games:
        per_seed.append({
            'seed': int(_g.seed),
            'score': int(_g.score),
            'max_tile': int(_g.max_tile),
            'moves': int(_g.moves),
            'state': str(_g.final_state),
            'walltime_sec': round(_g.walltime_sec, 4),
            'err': _err_for_final_state(_g.final_state),
        })
    obs['per_seed'] = per_seed
    obs['mean'] = float(_attempt.mean_score)
    obs['median'] = float(_attempt.median_score)
    obs['max_tile_best'] = int(_attempt.max_max_tile)
    obs['walltime_sec_total'] = round(_attempt.aggregate_walltime_sec, 4)
    return '<observation>' + _json.dumps(obs) + '</observation>'


def _err_for_final_state(final_state):
    """Cycle 70: map GameResult.final_state to the optional `err` field
    in the execute_submission per_seed observation. None for happy
    states; descriptive string for sentinel states so the model can
    read why a per_seed entry is degenerate."""
    if final_state in ('won', 'lost'):
        return None
    if final_state == 'walltime_exceeded':
        return 'walltime_exceeded (per-game cap from DEV_HARD_WALL_S budget)'
    if final_state == 'solver_error':
        return 'solver_error (Solver raised in __init__ or move)'
    if final_state == 'stagnated':
        return 'stagnated (no progress detected)'
    return f'sentinel: {final_state}'



SYSTEM_PROMPT = """You are an expert Python engineer competing in reward-bench Tier 1 — the 2048 FSM-solver task.

You have read access to the task spec and the env source, and write access to /workspace.

Tool calls go in fenced code blocks tagged `tool` with a JSON body. One or more per turn. Examples:

```tool
{"name": "view", "args": {"path": "/tasks/2048/SKILL_tier1.md"}}
```
  Read a file (paths must start with /workspace, /env, or /tasks).

```tool
{"name": "execute_submission", "args": {}}
===FILE_BODY===
from __future__ import annotations
from transitions import Machine
class Solver:
    def __init__(self): ...
    def move(self, board: list[list[int]]) -> str:
        return 'W'
```
  PRIMARY TOOL (per ADR 0008). Emit your FULL submission body inline
  after the `===FILE_BODY===` separator (NO JSON escaping — newlines,
  quotes, backslashes all literal). The bench writes the body into a
  sandboxed Docker container, runs dev_runner on 5 dev seeds, and
  returns a structured JSON observation:

      <observation>{"protocol_violations": [...], "per_seed": [...],
                    "mean": <float>, "max_tile_best": <int>,
                    "walltime_sec_total": <float>}</observation>

  - protocol_violations: empty when your code follows the
    SKILL_tier1.md contract (class Solver + move(board) -> W/A/S/D).
    Non-empty = your submission was rejected; fix and resubmit.
  - per_seed: per-game record with score, max_tile, moves, state, err.
    Empty list when protocol_violations non-empty.
  - mean: dev-seed mean score. Use this as your improvement signal.

  Call repeatedly: each call writes the body fresh; previous body
  is discarded. IMPORTANT: do NOT use `===FILE_BODY===` anywhere
  inside the file body itself — it's a parser separator.

```tool
{"name": "finish", "args": {"note": "why you're done"}}
```
  Stop. The body of your most recent successful execute_submission
  (with non-empty per_seed) is promoted to /workspace/submission.py
  and scored on canonical seeds (different from dev seeds).

LEGACY TOOLS (kept behind --legacy-write-file until ADR 0007 is
superseded; prefer execute_submission):

```tool
{"name": "write_file", "args": {"path": "/workspace/submission.py"}}
===FILE_BODY===
... your full file ...
```
  Legacy: overwrite a file under /workspace. Use execute_submission instead.

```tool
{"name": "bash", "args": {"cmd": "python3 /tasks/2048/dev_runner.py /workspace/submission.py"}}
```
  Legacy: run dev_runner against the file written by write_file.
  Use execute_submission instead (single tool, sandboxed, structured output).

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


FIRST_USER = "Start the task. Read /tasks/2048/SKILL_tier1.md to learn the constraints, then optionally /env/env_2048.py for env details, then write your submission to /workspace/submission.py and iterate. Use the fenced-block JSON tool format the system prompt described."


def _call_model(vllm_base_url, vllm_api_key, messages, max_tokens=12288, temperature=0.0,
                model_id='qwen3.6-27b-awq'):
    # Cycle 74: model_id is the served name vLLM advertises. Default
    # preserves cycle-11 hardcoded behaviour for back-compat with old
    # callers; main()/run_loop now pass the target.served_name through
    # so a swapped container actually gets the right model name in
    # the payload (otherwise vLLM returns HTTP 404).
    payload = json.dumps({
        'model': model_id,
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
             supervisor=None, supervisor_every_k=0,
             agent_loop_wall_sec=0.0, max_no_tool_call_iters=0,
             finish_floor=0.0, model_id='qwen3.6-27b-awq'):
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
    # Cycle 34: accumulator for supervisor sweep samples per ADR 0005.
    _sweep_samples = []
    # Cycle 38: stall detection state.
    import time as _t_loop
    _loop_start = _t_loop.monotonic()
    _consecutive_no_tool_iters = 0
    # Cycle 48 / hypothesis #1: best-snapshot + restore. Track best dev MEAN
    # seen so far; snapshot submission.py -> submission.best.py on new best;
    # restore the snapshot over submission.py at finish so canonical scoring
    # sees the high-water mark, not whatever the model wrote last.
    _best_dev_mean = None
    _best_snapshot_path = workspace / 'submission.best.py'
    _submission_path = workspace / 'submission.py'
    # Cycle 65 / ADR 0008 finish-time promotion: remember the last
    # execute_submission body whose observation had per_seed != [] so it
    # can be written to workspace/submission.py at end-of-loop.
    _last_successful_execute_body = None
    while iter_n < max_iters and not finished:
        _iter_start = _t_loop.monotonic()
        iter_n += 1
        messages = list(condense(tuple(messages)))
        reply = _call_model(vllm_base_url, vllm_api_key, messages,
                            temperature=temperature, model_id=model_id)
        messages.append({'role': 'assistant', 'content': reply})
        tool_calls = parse_tool_calls(reply)
        if not tool_calls:
            obs = ('<error>no tool calls found in your reply. Each tool call '
                   'must be in a fenced code block tagged `tool`.</error>')
            messages.append({'role': 'user', 'content': obs})
            _consecutive_no_tool_iters += 1
            # Cycle 38: heartbeat for the no-tool-call path too.
            print(f'[run_loop] iter {iter_n}/{max_iters} '
                  f'tool_calls=0 no_tool_streak={_consecutive_no_tool_iters} '
                  f'dt={_t_loop.monotonic() - _iter_start:.2f}s', flush=True)
            if (max_no_tool_call_iters > 0
                    and _consecutive_no_tool_iters >= max_no_tool_call_iters):
                # No-progress stall: model emitting prose only for K iters.
                break
            if (agent_loop_wall_sec > 0
                    and _t_loop.monotonic() - _loop_start >= agent_loop_wall_sec):
                break
            continue
        _consecutive_no_tool_iters = 0
        observations = []
        for name, tool_args in tool_calls:
            # Cycle 50 / hypothesis #2: finish-floor enforcement. Reject
            # `finish` when best_dev_mean is below the floor; force the
            # model to keep iterating until it scores above the baseline.
            if name == 'finish' and finish_floor > 0:
                _best_str = (str(_best_dev_mean) if _best_dev_mean is not None
                             else 'unknown (no dev_runner yet)')
                if _best_dev_mean is None or _best_dev_mean < finish_floor:
                    rejected = (
                        f'<error>finish rejected: best dev MEAN so far is '
                        f'{_best_str}, which is below the finish_floor '
                        f'({finish_floor}). You must produce a submission '
                        f'scoring above this floor before finishing. '
                        f'Run `bash python3 /tasks/2048/dev_runner.py '
                        f'/workspace/submission.py` to test, then refine '
                        f'your FSM until dev MEAN exceeds {finish_floor}.'
                        f'</error>'
                    )
                    observations.append(rejected)
                    print(f'[harness] finish rejected '
                          f'(best_dev_mean={_best_str} < floor={finish_floor})',
                          flush=True)
                    continue
            obs = execute_tool(name, tool_args, workspace, env_dir, tasks_dir)
            observations.append(obs)
            # Cycle 65: track last successful execute_submission body for
            # finish-time promotion per ADR 0008.
            if name == 'execute_submission':
                _body_candidate = tool_args.get('content', '')
                if _body_candidate and _execute_submission_observation_is_successful(obs):
                    _last_successful_execute_body = _body_candidate
            if name == 'finish':
                finished = True
        messages.append({'role': 'user', 'content': '\n\n'.join(observations)})
        # Cycle 34: parse the iteration's observations for a dev_runner
        # summary line; record a Sample or a zero-filled placeholder.
        _parsed = None
        for _obs in observations:
            _parsed = _parse_dev_runner_summary(_obs)
            if _parsed is not None:
                break
        if _parsed is None:
            _sweep_samples.append((iter_n, 0.0, 0, 0.0))
        else:
            _mean, _max_tile, _walltime = _parsed
            _sweep_samples.append((iter_n, _mean, _max_tile, _walltime))
            # Cycle 48 / hypothesis #1: best-snapshot. New best dev MEAN ->
            # copy current submission.py to submission.best.py.
            if _best_dev_mean is None or _mean > _best_dev_mean:
                _best_dev_mean = _mean
                if _submission_path.exists():
                    try:
                        shutil.copyfile(_submission_path, _best_snapshot_path)
                        print(f'[harness] new best dev MEAN={_mean} (snapshot=True)',
                              flush=True)
                    except Exception:
                        pass
                else:
                    print(f'[harness] new best dev MEAN={_mean} '
                          f'(snapshot=False, no submission.py)',
                          flush=True)
        # Cycle 33 (ADR 0005): supervisor hook. Every K iters, ask the
        # supervisor whether to stop. We feed it a minimal per-iter sample
        # `(iter_n, 0.0, 0, 0.0)` for now — cycle 34 will parse real
        # dev_runner output into mean_score / max_tile.
        # Cycle 38: heartbeat after tool execution.
        print(f'[run_loop] iter {iter_n}/{max_iters} '
              f'tool_calls={len(tool_calls)} finished={finished} '
              f'dt={_t_loop.monotonic() - _iter_start:.2f}s '
              f'total={_t_loop.monotonic() - _loop_start:.1f}s', flush=True)
        # Cycle 38: agent-loop wall-time budget (mirrors ADR 0006 layer 1
        # but for the AGENT phase). Checked BETWEEN iterations to bound
        # total wall time on a stuck or runaway loop.
        if (agent_loop_wall_sec > 0
                and _t_loop.monotonic() - _loop_start >= agent_loop_wall_sec
                and not finished):
            break
        if (supervisor is not None
                and supervisor_every_k > 0
                and iter_n % supervisor_every_k == 0
                and not finished):
            sweep = tuple(_sweep_samples)
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
    # Cycle 48 / hypothesis #1: restore best snapshot over submission.py
    # so canonical scoring sees the best version the model produced this trial.
    if _best_snapshot_path.exists():
        try:
            shutil.copyfile(_best_snapshot_path, _submission_path)
            print(f'[harness] restored submission.best.py '
                  f'(dev MEAN={_best_dev_mean}) to submission.py for scoring',
                  flush=True)
        except Exception:
            pass
    # Cycle 65 / ADR 0008 finish-time promotion: write the last successful
    # execute_submission body to workspace/submission.py so canonical
    # scoring (which reads exactly that path) sees it.
    if _last_successful_execute_body is not None:
        try:
            # Ensure trailing newline (PEP-8 / Python convention). The
            # tool-call body parser strips the final \\n adjacent to the
            # closing ``` fence; restore it on promotion.
            _body = _last_successful_execute_body
            if not _body.endswith(chr(10)):
                _body = _body + chr(10)
            _submission_path.write_text(_body)
            print('[harness] promoted last successful execute_submission body '
                  'to workspace/submission.py for canonical scoring',
                  flush=True)
        except Exception:
            pass
    return {'iterations': iter_n, 'messages': messages, 'finished': finished}


def _execute_submission_observation_is_successful(obs):
    """Cycle 65 helper: ADR 0008 says 'successful' = per_seed != [].
    Returns False on any parse failure (defensive)."""
    if '<observation>' not in obs:
        return False
    try:
        import json as _json
        start = obs.index('<observation>') + len('<observation>')
        end = obs.index('</observation>', start)
        payload = _json.loads(obs[start:end])
        return isinstance(payload, dict) and bool(payload.get('per_seed'))
    except Exception:
        return False
