# `test_when_submission_source_imports_transitions_then_no_transitions_violation`
## Behaviour
Negative-control for body with 'from transitions import Machine'
 yields no transitions-related violation.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/tier1/test_harness.py`](../../../../tests/tier1/test_harness.py)::`test_when_submission_source_imports_transitions_then_no_transitions_violation`.
## Runtime scope
> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.
