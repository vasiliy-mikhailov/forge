# `test_when_run_loop_called_with_protocol_parser_then_extract_goes_through_port`
## Behaviour
extract() decodes
 replies instead of the module-level parse_tool_calls.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/tier1/test_run_loop_di.py`](../../../../tests/tier1/test_run_loop_di.py)::`test_when_run_loop_called_with_protocol_parser_then_extract_goes_through_port`.
## Runtime scope
> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.
