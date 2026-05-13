"""End-to-end bench test. See tests-spec/reward_bench/frameworks/main/."""
from src.tier1.entities.attempt_result import AttemptResult


def test_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_has_positive_mean_score():
    # Arrange
    from src.reward_bench.frameworks.main import main

    # Act
    result = main(model_id='qwen3.6-27b-awq')

    # Assert
    assert isinstance(result, AttemptResult)
    assert result.n_games == 20
    assert result.mean_score > 0, f'expected positive mean_score, got {result.mean_score}'
    assert len(result.games) == 20
    assert tuple(g.seed for g in result.games) == tuple(range(1000, 1020))
