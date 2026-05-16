# `test_when_main_signature_inspected_then_canonical_scorer_parameter_present`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

Cycle 105 sub-C: main() gains canonical_scorer DI parameter.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **no_fake** — exercises real bench seam offline (autouse fake bypassed).
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/reward_bench/frameworks/test_main_docker_scorer.py`](../../../../tests/reward_bench/frameworks/test_main_docker_scorer.py)::`test_when_main_signature_inspected_then_canonical_scorer_parameter_present`.

## Runtime scope

> **Runtime scope**: unit only — framework orchestration; production-runtime coverage via canonical bench (run_canonical_battery) and @smoke multi-model battery.

