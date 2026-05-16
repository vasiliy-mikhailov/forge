# `test_when_agent_loop_tool_schemas_imported_then_equals_registry_schemas`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Cycle 98c: TOOL_SCHEMAS module-level export still resolves so
    pre-cycle-98c callers (including the _call_model shim) keep working.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/adapters/test_tier1_tool_registry.py`](../../../../tests/adapters/test_tier1_tool_registry.py)::`test_when_agent_loop_tool_schemas_imported_then_equals_registry_schemas`.
