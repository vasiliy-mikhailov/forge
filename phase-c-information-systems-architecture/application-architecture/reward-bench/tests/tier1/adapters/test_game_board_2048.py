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
