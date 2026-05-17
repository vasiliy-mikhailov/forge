# `test_when_main_invoked_with_canonical_scorer_then_scorer_score_called`
## Behaviour
sub-C: injected canonical_scorer is what's used for scoring.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/reward_bench/frameworks/test_main_docker_scorer.py`](../../../../tests/reward_bench/frameworks/test_main_docker_scorer.py)::`test_when_main_invoked_with_canonical_scorer_then_scorer_score_called`.
## Runtime scope
> **Runtime scope**: unit only — framework orchestration; production-runtime coverage via canonical bench (run_canonical_battery) and @smoke multi-model battery.
