# `test_when_main_default_canonical_scorer_is_docker_canonical_scorer`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Cycle 105 sub-C: when canonical_scorer is omitted, main() builds
    a DockerCanonicalScorer lazily.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/reward_bench/frameworks/test_main_docker_scorer.py`](../../../../tests/reward_bench/frameworks/test_main_docker_scorer.py)::`test_when_main_default_canonical_scorer_is_docker_canonical_scorer`.
