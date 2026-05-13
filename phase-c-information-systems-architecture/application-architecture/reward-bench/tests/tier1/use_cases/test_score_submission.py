"""score_submission use-case tests.

See tests-spec/tier1/use_cases/score_submission/."""
from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.entities.game_result import GameResult
from src.tier1.use_cases.score_submission import score_submission


class _StubEnv:
    """Returns hand-crafted GameResult instances by seed so the test
    controls final_state and can pin the derivation of the boolean
    flags without a live game env."""

    _BY_SEED = {
        1: GameResult(seed=1, score=100, max_tile=64, moves=50,
                      final_state='stagnated', walltime_sec=0.01),
        2: GameResult(seed=2, score=200, max_tile=128, moves=80,
                      final_state='lost', walltime_sec=0.02),
    }

    def play_one_game(self, solver, seed):
        return self._BY_SEED[seed]


def test_when_score_submission_called_then_attempt_result_carries_per_game_records_and_derived_flags():
    # Arrange
    env = _StubEnv()

    # Act
    result = score_submission(
        solver_factory=lambda: object(),
        seeds=[1, 2],
        env=env,
    )

    # Assert
    assert isinstance(result, AttemptResult)
    assert len(result.games) == 2
    assert result.games[0].seed == 1
    assert result.games[1].seed == 2
    assert result.stagnated_any is True
    assert result.walltime_exceeded is False
