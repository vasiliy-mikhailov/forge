# `test_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply`

Pins the [ADR 0003 default knobs](../../../../docs/adr/0003-bench-defaults-500-iters-10-trials-temp-0.7.md)
on the `BenchConfig` entity: 500 iters, 10 trials, temperature 0.7,
no-improve never triggers (999999), finish-floor 0. These are what
every leaderboard publication runs under unless explicitly overridden.

- **Arrange**: import `BenchConfig`.
- **Act**: construct `BenchConfig()` with no arguments.
- **Assert**:
  - `cfg.max_iters == 500`.
  - `cfg.n_trials == 10`.
  - `cfg.temperature == 0.7`.
  - `cfg.max_no_improve == 999999`.
  - `cfg.finish_floor == 0.0`.
  - Frozen dataclass: attempted mutation raises `FrozenInstanceError`.

A second test case pins **override** behavior: every field can be
overridden in the constructor, and the override values read back.

Test code: [`tests/reward_bench/entities/test_bench_config.py`](../../../../tests/reward_bench/entities/test_bench_config.py).
