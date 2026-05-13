"""TierSpec tests. See tests-spec/reward_bench/entities/tier_spec/."""
from src.reward_bench.entities.tier_spec import TierSpec


def test_when_tier_spec_constructed_then_fields_preserved():
    # Arrange
    submission_shape = 'class Solver with move(board) -> W|A|S|D (transitions FSM)'

    # Act
    t = TierSpec(
        tier=1,
        image='reward-bench-tier1:${VERSION}',
        network_policy='none',
        submission_shape=submission_shape,
        reward_n=20,
        replay_tolerance_pct=0.0,
    )

    # Assert
    assert t.tier == 1
    assert t.image == 'reward-bench-tier1:${VERSION}'
    assert t.network_policy == 'none'
    assert t.submission_shape == submission_shape
    assert t.reward_n == 20
    assert t.replay_tolerance_pct == 0.0
