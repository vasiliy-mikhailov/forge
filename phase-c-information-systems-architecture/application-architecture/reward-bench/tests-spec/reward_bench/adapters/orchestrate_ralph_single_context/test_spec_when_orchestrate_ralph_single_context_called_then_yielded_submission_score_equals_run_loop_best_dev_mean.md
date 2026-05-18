# `test_when_orchestrate_ralph_single_context_called_then_yielded_submission_score_equals_run_loop_best_dev_mean`

Pins the score field of the §7 ralph adapter — the first
`Orchestrator` implementation per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md):

    orchestrate_ralph_single_context :: Env -> BenchConfig -> [Submission]

The adapter wraps `src.tier1.agent_loop.run_loop` (the existing
long-context strategy) and translates its `{best_dev_mean, ...}`
dict return into a `Submission` value object. Pins the score field
mapping.

- **Arrange**: a `fake_run_loop_fn(**_)` that ignores kwargs and
  returns `{'best_dev_mean': 42.5, ...}`. Construct adapter with
  `run_loop_fn=fake_run_loop_fn`. Minimal `Env` and default
  `BenchConfig()`.
- **Act**: `list(adapter.orchestrate(env, cfg))`.
- **Assert**: `submissions[0].score == 42.5`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_orchestrate_ralph_single_context_called_then_yielded_submission_score_equals_run_loop_best_dev_mean`.

## Model client injection point

- **Seam**: `run_loop_fn` constructor parameter.
- **Mode**: **fake** (default) — caller-provided fake.
- **Override**: pass real `run_loop` (defaults to `src.tier1.agent_loop.run_loop`).

## Runtime scope

> **Runtime scope**: unit only — field mapping with injected fake run_loop; no real loop, no Docker.
