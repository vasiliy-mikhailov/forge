# `test_when_bench_config_constructed_with_overrides_then_overrides_apply`

Pins that every `BenchConfig` field is overridable in the
constructor — important because tests pass smaller values than
[ADR 0003](../../../../docs/adr/0003-bench-defaults-500-iters-10-trials-temp-0.7.md)
to bound wall time. The override contract is the entity's only
escape hatch; if any field hardcoded its value, tests would be
stuck at 500 iters.

- **Arrange**: import `BenchConfig`.
- **Act**: construct `BenchConfig(max_iters=30, n_trials=1,
  temperature=0.0, max_no_improve=5, finish_floor=1000.0)`.
- **Assert**: every field reads back the overridden value
  (`30, 1, 0.0, 5, 1000.0`).

Companion to
[`test_spec_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply`](test_spec_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply.md)
— defaults pin ADR 0003, overrides pin the escape hatch.

Test code: [`tests/reward_bench/entities/test_bench_config.py`](../../../../tests/reward_bench/entities/test_bench_config.py).
