# `test_when_main_signature_inspected_then_canonical_scorer_parameter_present`

Pins that `main()` exposes a `canonical_scorer` DI parameter (default `None`) so tests can inject a recording scorer instead of spawning real Docker.

## Contract

- **Arrange**: import `main` and `inspect`.
- **Act**: read `inspect.signature(main).parameters`.
- **Assert**: `'canonical_scorer' in sig.parameters` AND `sig.parameters['canonical_scorer'].default is None`.

## Model client injection point

- **Seam**: none — pure function.
- **Mode**: `@pytest.mark.no_fake` — pure signature inspection.

Test code: [`../../../tests/reward_bench/frameworks/test_main_docker_scorer.py`](../../../tests/reward_bench/frameworks/test_main_docker_scorer.py)::`test_when_main_signature_inspected_then_canonical_scorer_parameter_present`.

## Runtime scope

> **Runtime scope**: unit only.
