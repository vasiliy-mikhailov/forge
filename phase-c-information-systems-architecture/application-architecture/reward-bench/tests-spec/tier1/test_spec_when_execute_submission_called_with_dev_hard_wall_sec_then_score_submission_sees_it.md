# `test_when_execute_submission_called_with_dev_hard_wall_sec_then_score_submission_sees_it`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Cycle 77 / ADR 0006: _execute_submission threads dev_hard_wall_sec
    through to score_submission's hard_wall_sec arg. Without this the
    cycle-77 alignment is unobservable.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py)::`test_when_execute_submission_called_with_dev_hard_wall_sec_then_score_submission_sees_it`.

## Runtime scope

> **Runtime scope**: unit only — tier1 use-case / parser contract; scale-invariant pure functions over Port mocks.

