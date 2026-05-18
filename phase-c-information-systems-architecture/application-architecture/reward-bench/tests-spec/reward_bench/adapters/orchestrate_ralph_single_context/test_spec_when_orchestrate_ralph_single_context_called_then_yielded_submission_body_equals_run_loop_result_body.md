# `test_when_orchestrate_ralph_single_context_called_then_yielded_submission_body_equals_run_loop_result_body`

Pins the body field of the §7 ralph adapter per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

The adapter reads `result['body']` from the `run_loop_fn` return
dict and stores it on the yielded `Submission`. The real
`run_loop` itself does not produce `'body'` in its return — a thin
wrapper around it lifts the workspace's `submission.best.py`
contents into the dict. That wrapper is a later cycle; this cycle
pins the mapping contract.

- **Arrange**: `fake_run_loop(**_)` returns a dict whose `'body'`
  key is `'class Solver: pass\n'` (plus the score / iterations /
  messages / finished plumbing).
- **Act**: `list(adapter.orchestrate(env, cfg))`.
- **Assert**: `submissions[0].body == 'class Solver: pass\n'`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_orchestrate_ralph_single_context_called_then_yielded_submission_body_equals_run_loop_result_body`.

## Model client injection point

- **Seam**: `run_loop_fn` constructor parameter.
- **Mode**: **fake** (default) — caller-provided fake.
- **Override**: pass real `run_loop` (defaults to `src.tier1.agent_loop.run_loop`).

## Runtime scope

> **Runtime scope**: unit only — field mapping with injected fake run_loop; no real loop, no Docker.
