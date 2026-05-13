"""TIER_REGISTRY tests. See tests-spec/reward_bench/use_cases/tier_registry/."""
from src.reward_bench.use_cases.tier_registry import TIER_REGISTRY


def test_when_tier_registry_inspected_then_four_tiers_match_spec_md():
    # Arrange (registry imported at module level)

    # Act
    tiers = list(TIER_REGISTRY)
    by_n = {t.tier: t for t in tiers}

    # Assert: shape
    assert len(tiers) == 4
    assert [t.tier for t in tiers] == [1, 2, 3, 4]

    # Tier 1 specifics from SPEC.md
    assert by_n[1].network_policy == 'none'
    assert by_n[1].reward_n == 20
    assert by_n[1].replay_tolerance_pct == 0.0

    # Tiers 2-4: vllm_only network, 10 games
    for n in (2, 3, 4):
        assert by_n[n].network_policy == 'vllm_only'
        assert by_n[n].reward_n == 10

    # Replay tolerance progression: 0, 5, 5, 10
    assert [by_n[n].replay_tolerance_pct for n in (1, 2, 3, 4)] == [0.0, 5.0, 5.0, 10.0]
