# `test_when_main_default_canonical_scorer_is_docker_canonical_scorer`
## Behaviour
sub-C: when canonical_scorer is omitted, main() builds
 a DockerCanonicalScorer lazily.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/reward_bench/frameworks/test_main_docker_scorer.py`](../../../../tests/reward_bench/frameworks/test_main_docker_scorer.py)::`test_when_main_default_canonical_scorer_is_docker_canonical_scorer`.
## Runtime scope
> **Runtime scope**: unit only — framework orchestration; production-runtime coverage via canonical bench (run_canonical_battery) and @smoke multi-model battery.
