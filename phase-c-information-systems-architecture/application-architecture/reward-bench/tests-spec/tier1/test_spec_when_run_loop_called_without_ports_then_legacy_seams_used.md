# `test_when_run_loop_called_without_ports_then_legacy_seams_used`
## Behaviour
back-compat: pre-cycle-99 callers (no ports passed)
 still go through the module-level _call_model / execute_tool /
 parse_tool_calls so existing monkeypatching tests stay green.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/tier1/test_run_loop_di.py`](../../../../tests/tier1/test_run_loop_di.py)::`test_when_run_loop_called_without_ports_then_legacy_seams_used`.
## Runtime scope
> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.
