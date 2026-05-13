"""AttemptResult tests. See tests-spec/tier1/entities/attempt_result/."""
from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.entities.game_result import GameResult


def test_when_attempt_result_constructed_with_games_tuple_then_games_field_preserves_tuple():
    # Arrange
    g1 = GameResult(seed=1000, score=7000, max_tile=512, moves=600,
                    final_state='lost', walltime_sec=0.15)
    g2 = GameResult(seed=1001, score=9000, max_tile=1024, moves=750,
                    final_state='lost', walltime_sec=0.20)

    # Act
    r = AttemptResult(
        games=(g1, g2),
        mean_score=8000.0,
        median_score=8000.0,
        std_score=1000.0,
        max_max_tile=1024,
        n_games=2,
        aggregate_walltime_sec=0.35,
        seeds=(1000, 1001),
    )

    # Assert
    assert r.games == (g1, g2)
    assert len(r.games) == 2
