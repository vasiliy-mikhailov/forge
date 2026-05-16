# `test_when_run_loop_called_with_tool_registry_then_dispatch_goes_through_port`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Cycle 99: passing tool_registry=R means R.dispatch() handles
    tool calls instead of the module-level execute_tool.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/tier1/test_run_loop_di.py`](../../../../tests/tier1/test_run_loop_di.py)::`test_when_run_loop_called_with_tool_registry_then_dispatch_goes_through_port`.

## Runtime scope

> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.

