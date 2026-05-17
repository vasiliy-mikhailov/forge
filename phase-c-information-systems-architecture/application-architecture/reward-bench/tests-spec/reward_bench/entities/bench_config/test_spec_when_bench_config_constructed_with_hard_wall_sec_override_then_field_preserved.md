# `test_when_bench_config_constructed_with_hard_wall_sec_override_then_field_preserved`
Pins that `BenchConfig` accepts a `hard_wall_sec` override and
reads it back. The companion default pin lives in
[`test_spec_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply`](test_spec_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply.md)
where `hard_wall_sec == 0.0` is added alongside the existing
default knobs.
Per [ layer 1](../../../../SOLUTION-ARCHITECTURE.md),
`score_submission` accepts a `hard_wall_sec` cap; the bench
composition root (`main()`) needs a way to pass that knob through.
`BenchConfig` is where every other input knob lives (max_iters,
n_trials, temperature, max_no_improve, finish_floor);
this cycle adds the missing one.
- **Arrange**: import `BenchConfig`.
- **Act**: construct `BenchConfig(hard_wall_sec=60.0)`.
- **Assert**: `cfg.hard_wall_sec == 60.0`.
Test code: [`tests/reward_bench/entities/test_bench_config.py`](../../../../tests/reward_bench/entities/test_bench_config.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.
