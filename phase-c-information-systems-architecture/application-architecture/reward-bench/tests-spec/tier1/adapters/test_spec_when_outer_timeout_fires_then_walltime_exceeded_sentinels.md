# `test_when_outer_timeout_fires_then_walltime_exceeded_sentinels`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

If subprocess.run raises TimeoutExpired (container exceeded the
    outer grace period), all seeds get walltime_exceeded sentinels.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/tier1/adapters/test_docker_canonical_scorer.py`](../../../../tests/tier1/adapters/test_docker_canonical_scorer.py)::`test_when_outer_timeout_fires_then_walltime_exceeded_sentinels`.

## Runtime scope

> **Runtime scope**: unit only — tier1 adapter contract; @live coverage at the production-scale boundary per the relevant cycle (123/124/125/128).

