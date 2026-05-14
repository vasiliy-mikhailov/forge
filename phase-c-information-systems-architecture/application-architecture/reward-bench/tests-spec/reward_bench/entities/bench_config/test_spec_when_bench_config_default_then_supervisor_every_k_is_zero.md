# `test_when_bench_config_default_then_supervisor_every_k_is_zero`

Adds `supervisor_every_k: int = 0` to [`BenchConfig`](
../../../../src-spec/reward_bench/entities/bench_config/src_spec_bench_config.md)
so [main()](../../../../src/reward_bench/frameworks/main.py) can read
the cadence per [ADR 0005](
../../../../docs/adr/0005-plateau-detection-supervisor-via-llm-self-judgment.md).

Default 0 = supervisor disabled (matches cycle-12 behavior; no
existing campaign data points are perturbed).

- **Arrange**: import `BenchConfig`.
- **Act**: `BenchConfig()` then `BenchConfig(supervisor_every_k=10)`.
- **Assert**:
  - `BenchConfig().supervisor_every_k == 0`.
  - `BenchConfig(supervisor_every_k=10).supervisor_every_k == 10`.

Test code: [`tests/reward_bench/entities/test_bench_config.py`](../../../../tests/reward_bench/entities/test_bench_config.py).
