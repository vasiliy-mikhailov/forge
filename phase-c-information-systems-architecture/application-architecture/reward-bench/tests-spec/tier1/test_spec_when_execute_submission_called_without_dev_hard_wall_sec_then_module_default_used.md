# `test_when_execute_submission_called_without_dev_hard_wall_sec_then_module_default_used`
## Behaviour
back-compat: dev_hard_wall_sec=None -> DEV_HARD_WALL_S (30s).
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py)::`test_when_execute_submission_called_without_dev_hard_wall_sec_then_module_default_used`.
## Runtime scope
> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.
