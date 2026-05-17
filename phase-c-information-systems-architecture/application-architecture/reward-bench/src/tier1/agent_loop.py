"""Tier 1 interactive agent loop."""
import json
import os
import re
import shutil
import urllib.request
from pathlib import Path



_TOOL_BLOCK_RE = re.compile(r'```tool\b\s*\n(.*?)\n```', re.DOTALL)
_BODY_SPLIT_RE = re.compile(r'\n===FILE_BODY===\s*\n', re.DOTALL)


def parse_tool_calls(reply, structured_tool_calls=None):
    """Extract tool calls from an assistant reply.

    Accepts (str, list|None) shape AND the composite reply shape.
    Constructs an `AssistantReply` dict and runs the production-default
    parser pair (fenced-text + structured-openai).
    """
    from src.ports.protocol_parser import AssistantReply
    from src.adapters.parsers.fenced_text_parser import FencedTextParser
    from src.adapters.parsers.structured_openai_parser import StructuredOpenAIParser
    from src.adapters.parsers.composite_parser import CompositeParser

    if isinstance(reply, dict):
        ar: AssistantReply = {
            'content': reply.get('content', '') or '',
            'tool_calls': reply.get('tool_calls') or (structured_tool_calls or []),
        }
    else:
        ar = {
            'content': reply or '',
            'tool_calls': structured_tool_calls or [],
        }

    parser = CompositeParser([FencedTextParser(), StructuredOpenAIParser()])
    calls = parser.extract(ar)
    return [(c.name, c.args) for c in calls]

def _trim(s, n=4000):
    if len(s) <= n:
        return s
    return s[: n - 200] + f"\n... [truncated, total {len(s)} chars]"


# Legacy bash dev_runner stdout summary:
#   MEAN=5000.0  MEDIAN=4800.0  max-tile-best=512  (1.5s total)
_DEV_RUNNER_SUMMARY_RE = re.compile(
    r"MEAN=([0-9]+(?:\.[0-9]+)?)\s+"
    r"MEDIAN=[0-9]+(?:\.[0-9]+)?\s+"
    r"max-tile-best=([0-9]+)\s+"
    r"\(([0-9]+(?:\.[0-9]+)?)s total\)"
)


def _parse_dev_runner_summary(obs_text):
    """Return (mean_score, max_tile, walltime_sec) or None.

    Matches both the legacy bash dev_runner stdout summary line and
    the execute_submission JSON observation wrapped in <observation>...</observation>.
    """
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
        except (ValueError, KeyError):
            pass
    m = _DEV_RUNNER_SUMMARY_RE.search(obs_text)
    if m is None:
        return None
    return (float(m.group(1)), int(m.group(2)), float(m.group(3)))




def execute_tool(name, args, workspace, env_dir, tasks_dir,
                 dev_hard_wall_sec: float = None):
    """Delegates to Tier1ToolRegistry."""
    from src.adapters.tier1_tool_registry import Tier1ToolRegistry
    registry = Tier1ToolRegistry()
    return registry.dispatch(name, args, {
        'workspace': workspace,
        'env_dir': env_dir,
        'tasks_dir': tasks_dir,
        'dev_hard_wall_sec': dev_hard_wall_sec,
    })

_DEV_SEEDS = (1, 2, 3, 4, 5)

# Aggregate wall-time cap for the dev feedback path.
DEV_HARD_WALL_S = 30.0


def _execute_submission(body, workspace, tasks_dir,
                        dev_hard_wall_sec: float = None):
    if dev_hard_wall_sec is None:
        dev_hard_wall_sec = DEV_HARD_WALL_S
    """Dispatcher. Always returns a JSON-string observation;
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
    violations = validate_submission_protocol(module, source=body)
    if violations:
        obs['protocol_violations'].extend(violations)
        return '<observation>' + _json.dumps(obs) + '</observation>'

    # Dev runner uses Docker hard-kill (cgroup) — in-process daemon-thread
    # soft timeout cannot interrupt C-level CPU-bound submissions.
    from src.tier1.adapters.docker_canonical_scorer import DockerCanonicalScorer
    try:
        _scorer = DockerCanonicalScorer(env_path=Path(tasks_dir) / 'env.py')
        _attempt = _scorer.score(
            sub_path,
            _DEV_SEEDS,
            hard_wall_sec=dev_hard_wall_sec,
        )
    except RuntimeError as e:
        # Infrastructure failure (image missing, daemon down) — surface
        # as protocol_violation so the model sees the failure.
        obs['protocol_violations'].append(
            f'dev runner infrastructure failure: {type(e).__name__}: {e}'
        )
        return '<observation>' + _json.dumps(obs) + '</observation>'
    except Exception as e:
        obs['protocol_violations'].append(
            f'DockerCanonicalScorer failed: {type(e).__name__}: {e}'
        )
        return '<observation>' + _json.dumps(obs) + '</observation>'

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
    """Map GameResult.final_state to the optional `err` field
    in the execute_submission per_seed observation."""
    if final_state in ('won', 'lost'):
        return None
    if final_state == 'walltime_exceeded':
        return 'walltime_exceeded (per-game cap from dev_hard_wall_sec budget)'
    if final_state == 'solver_error':
        return 'solver_error (Solver raised in __init__ or move)'
    if final_state == 'stagnated':
        return 'stagnated (no progress detected)'
    return f'sentinel: {final_state}'



# Re-exported for back-compat callers.
from src.adapters.tier1_tool_registry import Tier1ToolRegistry as _Tier1Reg
TOOL_SCHEMAS = _Tier1Reg().schemas


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
  PRIMARY TOOL. Emit your FULL submission body inline after the
  `===FILE_BODY===` separator (NO JSON escaping — newlines, quotes,
  backslashes all literal). The bench writes the body into a
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

You are in a ralph loop: execute_submission → observe → refine → repeat
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
    """Thin shim over VllmOpenAIClient."""
    from src.adapters.vllm_openai_client import VllmOpenAIClient
    client = VllmOpenAIClient(
        base_url=vllm_base_url,
        api_key=vllm_api_key,
        default_model_id=model_id,
    )
    return client.call(
        messages,
        tools=list(TOOL_SCHEMAS),
        temperature=temperature,
        max_tokens=max_tokens,
        model_id=model_id,
    )

def _identity_condense(messages):
    """Default condense: pass messages through unchanged."""
    return tuple(messages)


def run_loop(workspace, env_dir, tasks_dir, vllm_base_url, vllm_api_key,
             max_iters, condense=_identity_condense, temperature=0.0,
             supervisor=None, supervisor_every_k=0,
             agent_loop_wall_sec=0.0, max_no_tool_call_iters=0,
             finish_floor=0.0, model_id='qwen3.6-27b-awq',
             smoke_early_stop=False, dev_hard_wall_sec: float = None,
             max_tokens: int = 12288,
             model_client=None, tool_registry=None, protocol_parser=None):
    """Drive the interactive agent loop for at most max_iters turns.

    `condense` is an opaque callable that takes the message tuple and
    returns a (possibly shorter) tuple. Called BEFORE every _call_model
    invocation. Default is identity.

    `supervisor` is an optional SupervisorPort consulted every
    `supervisor_every_k` iterations. When the supervisor returns
    `stop_recommended=True`, the loop terminates early with
    `finished=True`.

    Returns {iterations, messages, finished, best_dev_mean}.
    """
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': FIRST_USER},
    ]
    finished = False
    iter_n = 0
    _sweep_samples = []
    import time as _t_loop
    _loop_start = _t_loop.monotonic()
    _consecutive_no_tool_iters = 0
    # Best-snapshot + restore: track best dev MEAN, snapshot submission.py
    # on new best, restore at finish for canonical scoring.
    _best_dev_mean = None
    _best_snapshot_path = workspace / 'submission.best.py'
    _submission_path = workspace / 'submission.py'
    _last_successful_execute_body = None
    while iter_n < max_iters and not finished:
        _iter_start = _t_loop.monotonic()
        iter_n += 1
        messages = list(condense(tuple(messages)))
        if model_client is not None:
            _tools = (list(tool_registry.schemas) if tool_registry is not None
                      else list(TOOL_SCHEMAS))
            reply = model_client.call(
                messages, tools=_tools, temperature=temperature,
                max_tokens=max_tokens, model_id=model_id,
            )
        else:
            reply = _call_model(vllm_base_url, vllm_api_key, messages,
                                temperature=temperature, model_id=model_id,
                                max_tokens=max_tokens)
        # Mocked _call_model in old tests returns a bare string; wrap.
        if isinstance(reply, str):
            reply = {'content': reply, 'tool_calls': []}
        _content = reply.get('content', '') or ''
        _structured = reply.get('tool_calls') or []
        messages.append({'role': 'assistant', 'content': _content})
        if protocol_parser is not None:
            _ar = {'content': _content, 'tool_calls': _structured or []}
            _calls = protocol_parser.extract(_ar)
            tool_calls = [(c.name, c.args) for c in _calls]
        else:
            tool_calls = parse_tool_calls(_content, structured_tool_calls=_structured)
        if not tool_calls:
            obs = ('<error>no tool calls found in your reply. Each tool call '
                   'must be in a fenced code block tagged `tool`.</error>')
            messages.append({'role': 'user', 'content': obs})
            _consecutive_no_tool_iters += 1
            print(f'[run_loop] iter {iter_n}/{max_iters} '
                  f'tool_calls=0 no_tool_streak={_consecutive_no_tool_iters} '
                  f'dt={_t_loop.monotonic() - _iter_start:.2f}s', flush=True)
            if (max_no_tool_call_iters > 0
                    and _consecutive_no_tool_iters >= max_no_tool_call_iters):
                break
            if (agent_loop_wall_sec > 0
                    and _t_loop.monotonic() - _loop_start >= agent_loop_wall_sec):
                break
            continue
        _consecutive_no_tool_iters = 0
        observations = []
        for name, tool_args in tool_calls:
            # Finish-floor enforcement: reject `finish` when best_dev_mean
            # is below the floor.
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
            if tool_registry is not None:
                obs = tool_registry.dispatch(name, tool_args, {
                    'workspace': workspace, 'env_dir': env_dir,
                    'tasks_dir': tasks_dir,
                    'dev_hard_wall_sec': dev_hard_wall_sec,
                })
            else:
                obs = execute_tool(name, tool_args, workspace, env_dir, tasks_dir,
                                   dev_hard_wall_sec=dev_hard_wall_sec)
            observations.append(obs)
            if name == 'execute_submission':
                _body_candidate = tool_args.get('content', '')
                if _body_candidate and _execute_submission_observation_is_successful(obs):
                    _last_successful_execute_body = _body_candidate
            if name == 'finish':
                finished = True
        messages.append({'role': 'user', 'content': '\n\n'.join(observations)})
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
            # Smoke-mode bench-forced early-stop.
            if smoke_early_stop and _best_dev_mean is not None and _best_dev_mean > 0:
                finished = True
                print(f'[run_loop] smoke_early_stop fired at iter {iter_n} '
                      f'with best dev MEAN={_best_dev_mean}',
                      flush=True)
        print(f'[run_loop] iter {iter_n}/{max_iters} '
              f'tool_calls={len(tool_calls)} finished={finished} '
              f'dt={_t_loop.monotonic() - _iter_start:.2f}s '
              f'total={_t_loop.monotonic() - _loop_start:.1f}s', flush=True)
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
    # Restore best-snapshot so canonical scoring sees the high-water-mark body.
    if _best_snapshot_path.exists():
        try:
            shutil.copyfile(_best_snapshot_path, _submission_path)
            print(f'[harness] restored submission.best.py '
                  f'(dev MEAN={_best_dev_mean}) to submission.py for scoring',
                  flush=True)
        except Exception:
            pass
    # Fallback: promote last successful execute_submission body when no snapshot.
    if _last_successful_execute_body is not None and not _best_snapshot_path.exists():
        try:
            _body = _last_successful_execute_body
            if not _body.endswith(chr(10)):
                _body = _body + chr(10)
            _submission_path.write_text(_body)
            print('[harness] promoted last successful execute_submission body '
                  'to workspace/submission.py for canonical scoring',
                  flush=True)
        except Exception:
            pass
    return {'iterations': iter_n, 'messages': messages,
            'finished': finished, 'best_dev_mean': _best_dev_mean}


def _execute_submission_observation_is_successful(obs):
    """'successful' = per_seed != []. Returns False on any parse failure."""
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
