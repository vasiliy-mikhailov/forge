# `test_when_tier_spec_constructed_then_fields_preserved`
Pins the `TierSpec` data contract. Construct one and assert every
field reads back exactly.
- **Arrange**: import `TierSpec`.
- **Act**: construct
 `TierSpec(tier=1, image='reward-bench-tier1:${VERSION}',
 network_policy='none',
 submission_shape='class Solver with move(board) -> W|A|S|D (transitions FSM)',
 reward_n=20, replay_tolerance_pct=0.0)`.
- **Assert**: every field reads back its constructor value.
Test code: [`tests/reward_bench/entities/test_tier_spec.py`](../../../../tests/reward_bench/entities/test_tier_spec.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.
