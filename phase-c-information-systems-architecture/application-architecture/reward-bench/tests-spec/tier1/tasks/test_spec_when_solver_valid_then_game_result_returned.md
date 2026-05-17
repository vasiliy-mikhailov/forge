# `test_when_solver_valid_then_game_result_returned`
## Behaviour
sub-A worker: valid Solver -> game played, dict returned.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/tier1/tasks/test_runner_canonical.py`](../../../../tests/tier1/tasks/test_runner_canonical.py)::`test_when_solver_valid_then_game_result_returned`.
## Runtime scope
> **Runtime scope**: unit only — runner_canonical worker contracts; live coverage via @live test_docker_canonical_scorer_live which invokes runner_canonical inside Docker against a real solver.
