"""Tier 1 scorer. See src-spec/tier1/src_spec_when_solver_plays_*.md."""
import sys
from pathlib import Path


_TASKS = Path(__file__).resolve().parents[2] / 'tasks/2048'
if str(_TASKS) not in sys.path:
    sys.path.insert(0, str(_TASKS))

from env import GameBoard  # noqa: E402


def score_one_game(solver, seed):
    board = GameBoard(seed=seed)
    while not board.is_terminal():
        action = solver.move(board.board)
        board.do_action(action)
    return board.score
