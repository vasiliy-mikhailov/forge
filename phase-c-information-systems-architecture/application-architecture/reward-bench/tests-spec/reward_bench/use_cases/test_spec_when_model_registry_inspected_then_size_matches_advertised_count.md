# `test_when_model_registry_inspected_then_size_matches_advertised_count`
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: n = len(MODEL_REGISTRY)
- **Assert**: assert n == 22, f'expected 22 entries in MODEL_REGISTRY, got {n}'
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/reward_bench/use_cases/test_model_registry.py`](../../../../tests/reward_bench/use_cases/test_model_registry.py)::`test_when_model_registry_inspected_then_size_matches_advertised_count`.
## Runtime scope
> **Runtime scope**: unit only — use-case orchestration over Port mocks; scale-invariant.
