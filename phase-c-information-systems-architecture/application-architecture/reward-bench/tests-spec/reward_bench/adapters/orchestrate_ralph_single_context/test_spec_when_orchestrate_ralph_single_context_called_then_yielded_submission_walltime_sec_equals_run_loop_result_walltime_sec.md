# `test_when_orchestrate_ralph_single_context_called_then_yielded_submission_walltime_sec_equals_run_loop_result_walltime_sec`

Pins the walltime field of the §7 ralph adapter per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

The adapter reads `result['walltime_sec']` from the `run_loop_fn`
return dict and stores it on the yielded `Submission`. The fitness
test `best_score env cfg t` filters Submissions by walltime against
a budget; that filter is meaningless without this field.

- **Arrange**: `fake_run_loop(**_)` returns a dict whose
  `'walltime_sec'` key is `137.25` (plus body / score plumbing).
- **Act**: `list(adapter.orchestrate(env, cfg))`.
- **Assert**: `submissions[0].walltime_sec == 137.25`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_orchestrate_ralph_single_context_called_then_yielded_submission_walltime_sec_equals_run_loop_result_walltime_sec`.

## Model client injection point

- **Seam**: `run_loop_fn` constructor parameter.
- **Mode**: **fake** (default) — caller-provided fake.
- **Override**: pass real `run_loop` (defaults to `src.tier1.agent_loop.run_loop`).

## Runtime scope

> **Runtime scope**: unit only — field mapping with injected fake run_loop; no real loop, no Docker.
