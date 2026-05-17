# `test_when_bench_config_default_then_supervisor_every_k_is_zero`
Adds `supervisor_every_k: int = 0` to [`BenchConfig`](../../../../src-spec/reward_bench/entities/bench_config/src_spec_bench_config.md)
so [main()](../../../../src/reward_bench/frameworks/main.py) can read
the cadence per [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md).
Default 0 = supervisor disabled (matches cycle-12 behavior; no
existing campaign data points are perturbed).
- **Arrange**: import `BenchConfig`.
- **Act**: `BenchConfig()` then `BenchConfig(supervisor_every_k=10)`.
- **Assert**:
 - `BenchConfig().supervisor_every_k == 0`.
 - `BenchConfig(supervisor_every_k=10).supervisor_every_k == 10`.
Test code: [`tests/reward_bench/entities/test_bench_config.py`](../../../../tests/reward_bench/entities/test_bench_config.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.
