"""End-to-end bench test. See tests-spec/reward_bench/frameworks/main/."""
from src.tier1.entities.attempt_result import AttemptResult


def test_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted():
    # Arrange
    from src.reward_bench.frameworks.main import main

    # Act
    result = main(model_id='qwen3.6-27b-awq')

    # Assert: shape-only contract (model quality is a separate cycle)
    assert isinstance(result, AttemptResult)
    assert result.n_games == len(result.games)
    assert result.aggregate_walltime_sec >= 0.0
    if result.n_games == 20:
        # Happy path: scored 20 canonical seeds
        assert result.mean_score >= 0.0
        assert tuple(g.seed for g in result.games) == tuple(range(1000, 1020))
    else:
        # Sentinel: submission shape error
        assert result.n_games == 0
        assert len(result.games) == 0
