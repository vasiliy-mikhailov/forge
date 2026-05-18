# `test_when_run_loop_with_metrics_called_then_result_walltime_sec_equals_time_delta`

Pins the walltime measurement of the §7 ralph production wrapper per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

`run_loop_with_metrics` is the function that closes the contract gap
between the real `src.tier1.agent_loop.run_loop` (which returns no
walltime) and the `OrchestrateRalphSingleContext` adapter (which
reads `result['walltime_sec']`). It measures monotonic time around
the inner-loop call and injects the delta into the result dict.

- **Arrange**: a fake `_time_fn` whose first call returns `100.0`
  and second call returns `137.25`. A fake `_run_loop` ignoring
  kwargs and returning a minimal dict (no walltime_sec).
- **Act**: `run_loop_with_metrics(_run_loop=fake_run_loop, _time_fn=fake_time_fn)`.
- **Assert**: `result['walltime_sec'] == 37.25`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_run_loop_with_metrics_called_then_result_walltime_sec_equals_time_delta`.

## Model client injection point

- **Seam**: `_run_loop` and `_time_fn` keyword parameters.
- **Mode**: **fake** (default) — caller-provided fakes.
- **Override**: omit both — defaults to `src.tier1.agent_loop.run_loop` and `time.monotonic`.

## Runtime scope

> **Runtime scope**: unit only — time delta with injected clock and inner-loop stub; no real loop, no Docker.
