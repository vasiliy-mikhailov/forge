"""GameBoard2048Adapter tests.

See tests-spec/tier1/adapters/game_board_2048/."""
from pathlib import Path

from src.tier1.adapters.game_board_2048 import GameBoard2048Adapter
from src.tier1.entities.game_result import GameResult
from src.tier1.harness import load_submission


REPO = Path(__file__).resolve().parents[3]


def test_when_game_board_2048_adapter_plays_one_game_then_returns_game_result_with_full_fields():
    # Arrange
    module = load_submission(REPO / 'tasks/2048/baselines/reference_fsm.py')
    adapter = GameBoard2048Adapter()

    # Act
    result = adapter.play_one_game(module.Solver(), seed=1000)

    # Assert
    assert isinstance(result, GameResult), f'expected GameResult, got {type(result).__name__}'
    assert result.seed == 1000
    assert result.score >= 0
    assert result.max_tile >= 2
    assert result.moves > 0
    assert result.final_state in ('won', 'lost')
    assert result.walltime_sec > 0.0



class _CrashingSolver:
    """Stub Solver whose move() raises AttributeError — reproduces campaign8."""
    def move(self, board):
        raise AttributeError("'to_opening' does not exist on <Machine@stub>")


def test_when_solver_raises_in_move_then_returns_game_result_with_final_state_solver_error():
    """Cycle 28 (no-silent-fix): adapter catches solver runtime errors and
    emits GameResult(final_state='solver_error') instead of propagating.

    Reproduces campaign8: AttributeError inside solver.move() escaped
    score_submission and failed the campaign with no partial leaderboard."""
    # Arrange
    adapter = GameBoard2048Adapter()
    solver = _CrashingSolver()

    # Act
    result = adapter.play_one_game(solver, seed=1)

    # Assert
    assert isinstance(result, GameResult), f'expected GameResult, got {type(result).__name__}'
    assert result.final_state == 'solver_error', (
        f"solver crash should yield 'solver_error' sentinel; got "
        f"{result.final_state!r}"
    )
    assert result.seed == 1
    assert result.moves == 0
    assert result.walltime_sec >= 0.0
    assert result.score >= 0
    assert result.max_tile >= 2
