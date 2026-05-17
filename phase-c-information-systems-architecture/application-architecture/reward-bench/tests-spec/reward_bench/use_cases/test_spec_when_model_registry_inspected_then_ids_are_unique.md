# `test_when_model_registry_inspected_then_ids_are_unique`
## Contract
- **Arrange**: ids = [t.id for t in MODEL_REGISTRY]
- **Act**: n_total = len(ids); n_unique = len(set(ids))
- **Assert**: assert n_total == n_unique, (; f'duplicate ids in MODEL_REGISTRY: '; f'{sorted({i for i in ids if ids.count(i) > 1})}';)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/reward_bench/use_cases/test_model_registry.py`](../../../../tests/reward_bench/use_cases/test_model_registry.py)::`test_when_model_registry_inspected_then_ids_are_unique`.
## Runtime scope
> **Runtime scope**: unit only — use-case orchestration over Port mocks; scale-invariant.
