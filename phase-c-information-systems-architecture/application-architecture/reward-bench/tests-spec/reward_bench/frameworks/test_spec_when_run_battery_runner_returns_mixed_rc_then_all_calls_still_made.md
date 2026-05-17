# `test_when_run_battery_runner_returns_mixed_rc_then_all_calls_still_made`
## Behaviour
A non-zero rc on one model does NOT short-circuit the battery.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/reward_bench/frameworks/test_run_battery.py`](../../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_run_battery_runner_returns_mixed_rc_then_all_calls_still_made`.
## Runtime scope
> **Runtime scope**: unit only — framework orchestration; production-runtime coverage via canonical bench (run_canonical_battery) and @smoke multi-model battery.
