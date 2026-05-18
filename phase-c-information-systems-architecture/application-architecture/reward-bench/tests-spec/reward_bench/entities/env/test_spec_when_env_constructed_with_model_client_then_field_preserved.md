# `test_when_env_constructed_with_model_client_then_field_preserved`

Pins the `Env.model_client` field per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7. Per the wrapper-encapsulation principle, URL strings
(`vllm_base_url`, `vllm_api_key`, `model_id`) do not belong in the
bench-side API. Env holds a pre-bound `ModelClient` instance; the
wrapper extracts/passes it through.

Default is `None` so the prior two-field constructor still works
for tests that don't need a model client.

- **Arrange**: import `Env` and `FakeModelClient`; build a fake.
- **Act**: `Env(tasks_dir=Path('/tmp/x'),
  canonical_scorer=FakeCanonicalScorer(), model_client=fake)`.
- **Assert**: `env.model_client is fake`.

Test code: [`../../../../tests/reward_bench/entities/test_env.py`](../../../../tests/reward_bench/entities/test_env.py)::`test_when_env_constructed_with_model_client_then_field_preserved`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — frozen-dataclass invariant; no runtime boundary involved.
