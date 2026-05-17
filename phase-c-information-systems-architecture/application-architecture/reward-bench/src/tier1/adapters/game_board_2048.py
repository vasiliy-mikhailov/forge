"""GameBoard2048Adapter: wraps tasks/2048/env.GameBoard behind GameEnvPort."""
import sys
import time
from pathlib import Path


_TASKS = Path(__file__).resolve().parents[3] / "tasks/2048"
if str(_TASKS) not in sys.path:
    sys.path.insert(0, str(_TASKS))

from env import GameBoard  # noqa: E402

from src.tier1.entities.game_result import GameResult


class GameBoard2048Adapter:
    """Concrete GameEnvPort over tasks/2048/env.GameBoard."""

    def play_one_game(self, solver, seed):
        board = GameBoard(seed=seed)
        moves = 0
        start = time.monotonic()
        # Catch solver runtime errors and emit a per-game sentinel
        # (final_state='solver_error') instead of letting the exception escape.
        try:
            while not board.is_terminal():
                action = solver.move(board.board)
                board.do_action(action)
                moves += 1
        except Exception:
            return GameResult(
                seed=seed,
                score=board.score,
                max_tile=board.max_tile,
                moves=moves,
                final_state='solver_error',
                walltime_sec=time.monotonic() - start,
            )
        walltime_sec = time.monotonic() - start
        # board.state is 'won' or 'lost' once terminal.
        final_state = board.state if board.state in ('won', 'lost') else 'lost'
        return GameResult(
            seed=seed,
            score=board.score,
            max_tile=board.max_tile,
            moves=moves,
            final_state=final_state,
            walltime_sec=walltime_sec,
        )
