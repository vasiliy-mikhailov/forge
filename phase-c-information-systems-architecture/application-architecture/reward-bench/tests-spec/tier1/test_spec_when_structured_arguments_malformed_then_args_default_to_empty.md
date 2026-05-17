# `test_when_structured_arguments_malformed_then_args_default_to_empty`
## Behaviour
defensive: bad JSON in structured arguments must not
 raise; we emit (name, {}) so the dispatcher's protocol-violation
 path handles it instead of crashing the run loop.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py)::`test_when_structured_arguments_malformed_then_args_default_to_empty`.
## Runtime scope
> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.
