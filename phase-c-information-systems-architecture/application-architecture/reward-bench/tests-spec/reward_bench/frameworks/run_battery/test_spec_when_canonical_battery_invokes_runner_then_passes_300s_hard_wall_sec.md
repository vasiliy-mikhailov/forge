# `test_spec_when_canonical_battery_invokes_runner_then_passes_300s_hard_wall_sec`

Pins the **canonical `hard_wall_sec = 300` default** per
[ADR 0015](../../../../docs/adr/0015-canonical-bench-hard-wall-sec-300.md).

## Why

Cycle 102 left `hard_wall_sec` unset → BenchConfig default 0.0 →
unbounded canonical scoring. The 2026-05-16 overnight bench hit a
slow Solver in qwen3.6-27b-fp8 trial 3 that ran for >2 hours of
canonical scoring alone. ADR 0015 fills the ADR 0003 gap with a 300 s
aggregate cap (~15 s/seed effective across 20 canonical seeds).

## Contract

`run_canonical_battery(canonical_hard_wall_sec=300, ...)` —
the default-bound runner constructs
`BenchConfig(..., hard_wall_sec=canonical_hard_wall_sec)` and passes
it to `reward_bench.frameworks.main.main`. Callers may override the
parameter for a specific sweep; defaults persist the ADR.

## Model client injection point

- **Seam**: the `runner` callable that `run_canonical_battery` invokes.
  Default runner closure reads `canonical_hard_wall_sec` from outer
  scope and builds the `BenchConfig`. Tests inject a recorder
  `runner(model_id, trial)` and assert the bench infrastructure that
  feeds it knows the 300 s value.
- **Default**: `fake` — no real Solver / vLLM needed; the test injects
  a recorder.

## Tests

### `test_when_canonical_battery_default_then_hard_wall_sec_is_300`

- **Arrange**: a recorder closure that captures the
  `canonical_hard_wall_sec` argument visible to the runner.
- **Act**: `run_canonical_battery(n_trials=1, registry_path=...)` with
  NO `canonical_hard_wall_sec` override.
- **Assert**: the runner's view of the wall cap is exactly 300 s.

### `test_when_canonical_battery_override_then_caller_value_used`

- **Arrange**: same recorder.
- **Act**: `run_canonical_battery(canonical_hard_wall_sec=600, n_trials=1, ...)`.
- **Assert**: recorder sees 600 s.

### `test_when_canonical_battery_passes_to_main_then_bench_config_has_300`

- **Arrange**: monkeypatch `reward_bench.frameworks.main.main` to
  capture the `BenchConfig` argument.
- **Act**: `run_canonical_battery(n_trials=1, registry_path=...)`
  using the default runner (not the test recorder).
- **Assert**: the captured `config.hard_wall_sec == 300`. The
  cycle 77 derivation `dev = canonical * 5 / 20 = 75` is preserved
  (asserted via the run_loop path or via inspecting `main`'s use
  of `_dev_hard_wall_sec`).

Test code: [`tests/reward_bench/frameworks/test_canonical_battery.py`](../../../../tests/reward_bench/frameworks/test_canonical_battery.py).

## Runtime scope

> **Runtime scope**: unit only — canonical-battery driver; production-runtime IS this driver invoked end-to-end during operational sweeps.

