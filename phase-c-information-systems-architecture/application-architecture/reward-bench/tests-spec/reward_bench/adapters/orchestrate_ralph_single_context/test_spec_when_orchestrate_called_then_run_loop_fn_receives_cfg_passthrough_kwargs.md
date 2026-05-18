# `test_when_orchestrate_called_then_run_loop_fn_receives_cfg_passthrough_kwargs`

Batches the remaining direct cfg→run_loop kwarg pass-throughs for
the §7 ralph adapter per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
Each kwarg flows from `BenchConfig` unchanged; the bench's
behaviour knobs all need to reach the loop.

Pins:

    temperature        ← cfg.temperature
    finish_floor       ← cfg.finish_floor
    supervisor_every_k ← cfg.supervisor_every_k
    smoke_early_stop   ← cfg.smoke_early_stop

`dev_hard_wall_sec` is derived (not a direct pass-through) and has
its own cycle.

- **Arrange**: `cfg = BenchConfig(temperature=0.5, finish_floor=0.3,
  supervisor_every_k=7, smoke_early_stop=True)`; recording
  `fake_run_loop` capturing kwargs; adapter built with the fake.
- **Act**: `list(adapter.orchestrate(env, cfg))`.
- **Assert**: each captured kwarg equals the corresponding cfg field.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_orchestrate_called_then_run_loop_fn_receives_cfg_passthrough_kwargs`.

## Model client injection point

- **Seam**: `run_loop_fn` constructor parameter (recording fake).
- **Mode**: **fake** — captures kwargs without spawning anything.

## Runtime scope

> **Runtime scope**: unit only — kwarg pass-through; no real loop.
