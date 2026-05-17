# `test_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply`
Pins the [ default knobs](../../../../SOLUTION-ARCHITECTURE.md)
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
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.

Test code: [`../../../../tests/reward_bench/entities/test_bench_config.py`](../../../../tests/reward_bench/entities/test_bench_config.py)::`test_when_bench_config_constructed_with_defaults_then_adr_0003_values_apply`.
