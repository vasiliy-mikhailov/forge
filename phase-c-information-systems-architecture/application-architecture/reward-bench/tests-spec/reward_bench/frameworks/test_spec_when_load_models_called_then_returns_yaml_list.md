# `test_when_load_models_called_then_returns_yaml_list`
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/reward_bench/frameworks/test_run_battery.py`](../../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_load_models_called_then_returns_yaml_list`.
## Runtime scope
> **Runtime scope**: unit only — framework orchestration; production-runtime coverage via canonical bench (run_canonical_battery) and @smoke multi-model battery.
