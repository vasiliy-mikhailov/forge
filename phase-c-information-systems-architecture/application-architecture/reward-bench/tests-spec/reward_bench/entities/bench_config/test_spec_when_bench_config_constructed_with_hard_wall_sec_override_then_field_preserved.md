# `test_when_bench_config_constructed_with_hard_wall_sec_override_then_field_preserved`

Pins that `BenchConfig` accepts a `hard_wall_sec` override and
reads it back. The companion default pin lives in
[`test_spec_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply`](test_spec_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply.md)
where `hard_wall_sec == 0.0` is added alongside the existing ADR 0003
default knobs.

Per [ADR 0006 layer 1](../../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md),
`score_submission` accepts a `hard_wall_sec` cap; the bench
composition root (`main()`) needs a way to pass that knob through.
`BenchConfig` is where every other input knob lives (max_iters,
n_trials, temperature, max_no_improve, finish_floor — cycle 16);
this cycle adds the missing one.

- **Arrange**: import `BenchConfig`.
- **Act**: construct `BenchConfig(hard_wall_sec=60.0)`.
- **Assert**: `cfg.hard_wall_sec == 60.0`.

Test code: [`tests/reward_bench/entities/test_bench_config.py`](../../../../tests/reward_bench/entities/test_bench_config.py).
