"""GameBoard2048Adapter: wraps tasks/2048/env.GameBoard behind GameEnvPort.

See src-spec/adapters/src_spec_game_board_2048_adapter.md."""
import sys
from pathlib import Path


_TASKS = Path(__file__).resolve().parents[2] / 'tasks/2048'
if str(_TASKS) not in sys.path:
    sys.path.insert(0, str(_TASKS))

from env import GameBoard  # noqa: E402


class GameBoard2048Adapter:
    """Concrete GameEnvPort over tasks/2048/env.GameBoard."""

    def play_one_game(self, solver, seed):
        board = GameBoard(seed=seed)
        while not board.is_terminal():
            action = solver.move(board.board)
            board.do_action(action)
        return board.score, board.max_tile
