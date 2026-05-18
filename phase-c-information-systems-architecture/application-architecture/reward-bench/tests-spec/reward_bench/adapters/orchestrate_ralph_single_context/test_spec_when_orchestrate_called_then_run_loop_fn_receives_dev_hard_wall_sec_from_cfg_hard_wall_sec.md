# `test_when_orchestrate_called_then_run_loop_fn_receives_dev_hard_wall_sec_from_cfg_hard_wall_sec`

Pins the simplest mapping of `dev_hard_wall_sec` for the §7 ralph
adapter per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md):
the inner run_loop receives `cfg.hard_wall_sec` directly as
`dev_hard_wall_sec`. This matches existing `main.py` behaviour when
the canonical scorer uses the default 5 seeds (where the original
derivation `hard_wall_sec * 5 / 5` reduces to identity).

The proper weighting (`* 5 / num_canonical_seeds`) and the 0→None
mapping are separate concerns deferred to later cycles when `Env`
grows to expose seed counts.

- **Arrange**: `cfg = BenchConfig(hard_wall_sec=60.0)`; recording
  fake; adapter with fake.
- **Act**: `list(adapter.orchestrate(env, cfg))`.
- **Assert**: `captured['dev_hard_wall_sec'] == 60.0`.

Test code: [`../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py`](../../../../tests/reward_bench/adapters/test_orchestrate_ralph_single_context.py)::`test_when_orchestrate_called_then_run_loop_fn_receives_dev_hard_wall_sec_from_cfg_hard_wall_sec`.

## Model client injection point

- **Seam**: `run_loop_fn` constructor parameter (recording fake).
- **Mode**: **fake** — captures kwargs without spawning anything.

## Runtime scope

> **Runtime scope**: unit only — kwarg pass-through; no real loop.
