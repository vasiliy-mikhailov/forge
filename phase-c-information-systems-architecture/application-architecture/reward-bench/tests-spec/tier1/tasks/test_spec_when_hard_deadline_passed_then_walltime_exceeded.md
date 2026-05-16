# `test_when_hard_deadline_passed_then_walltime_exceeded`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Deadline already passed at call time -> first iter of the
    game loop checks the wall clock and emits walltime_exceeded.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/tier1/tasks/test_runner_canonical.py`](../../../../tests/tier1/tasks/test_runner_canonical.py)::`test_when_hard_deadline_passed_then_walltime_exceeded`.

## Runtime scope

> **Runtime scope**: unit only — runner_canonical worker contracts; live coverage via @live test_docker_canonical_scorer_live (cycle 123) which invokes runner_canonical inside Docker against a real solver.

