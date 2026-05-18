# `test_when_orchestrate_called_then_run_loop_fn_receives_max_iters_from_cfg`

Pins the cfg→run_loop pass-through of `max_iters` for the §7 ralph
adapter per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
`max_iters` is the iter cap that bounds the long-context ralph
loop; without it, the loop runs to its default and the bench's
walltime budget is unhonored.

- **Arrange**: `cfg = BenchConfig(max_iters=42)`; recording
  `fake_run_loop` capturing kwargs; adapter built with the fake;
  minimal `env`.
- **Act**: `list(adapter.orchestrate(env, cfg))`.
- **Assert**: `captured['max_iters'] == 42`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_orchestrate_called_then_run_loop_fn_receives_max_iters_from_cfg`.

## Model client injection point

- **Seam**: `run_loop_fn` constructor parameter (recording fake).
- **Mode**: **fake** — captures kwargs without spawning anything.

## Runtime scope

> **Runtime scope**: unit only — kwarg pass-through; no real loop.
