# `test_when_play_one_game_raises_then_stdout_restored`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Cycle 103 defensive: exception in the worker must not leave
    stdout permanently redirected.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/tier1/use_cases/test_solver_stdout.py`](../../../../tests/tier1/use_cases/test_solver_stdout.py)::`test_when_play_one_game_raises_then_stdout_restored`.

## Runtime scope

> **Runtime scope**: unit only — use-case orchestration over Port mocks; scale-invariant by construction.

