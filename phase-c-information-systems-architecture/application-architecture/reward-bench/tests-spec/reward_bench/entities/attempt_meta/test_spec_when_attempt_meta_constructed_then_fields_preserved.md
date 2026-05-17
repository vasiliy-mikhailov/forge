# `test_when_attempt_meta_constructed_then_fields_preserved`
Pins the `AttemptMeta` data contract.
- **Arrange**: import `AttemptMeta`, set `started_at = datetime(...)`,
 `image_digest = 'sha256:<64-hex>'`, etc.
- **Act**: construct an `AttemptMeta` with concrete values.
- **Assert**: every field reads back its constructor value.
Test code: [`tests/reward_bench/entities/test_attempt_meta.py`](../../../../tests/reward_bench/entities/test_attempt_meta.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.

Test code: [`../../../../tests/reward_bench/entities/test_attempt_meta.py`](../../../../tests/reward_bench/entities/test_attempt_meta.py)::`test_when_attempt_meta_constructed_then_fields_preserved`.
