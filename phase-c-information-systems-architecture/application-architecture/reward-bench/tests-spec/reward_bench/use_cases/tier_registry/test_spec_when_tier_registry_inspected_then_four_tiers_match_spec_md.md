# `test_when_tier_registry_inspected_then_four_tiers_match_spec_md`
Pins the four-row TIER_REGISTRY against SPEC.md's tier specifications
table. Drift between the Python registry and SPEC.md surfaces
immediately.
- **Arrange**: import `TIER_REGISTRY` from
 `src.reward_bench.use_cases.tier_registry`.
- **Act**: inspect the tuple and each entry.
- **Assert**:
 - `len(TIER_REGISTRY) == 4`.
 - `[t.tier for t in TIER_REGISTRY] == [1, 2, 3, 4]`.
 - Tier 1 has `network_policy='none'`, `reward_n=20`,
 `replay_tolerance_pct=0.0`.
 - Tiers 2-4 all have `network_policy='vllm_only'` and
 `reward_n=10`.
 - Replay tolerance progression: 0, 5, 5, 10.
Test code: [`tests/reward_bench/use_cases/test_tier_registry.py`](../../../../tests/reward_bench/use_cases/test_tier_registry.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — TIER_REGISTRY tuple contract; pure-Python data; scale-invariant.
