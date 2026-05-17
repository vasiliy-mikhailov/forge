# `test_when_view_dispatched_with_missing_file_then_returns_not_found`
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/adapters/test_tier1_tool_registry.py`](../../../../tests/adapters/test_tier1_tool_registry.py)::`test_when_view_dispatched_with_missing_file_then_returns_not_found`.
## Runtime scope
> **Runtime scope**: unit only — adapter contract; the live coverage for the boundary it crosses lives in the adapter-specific @live test.
