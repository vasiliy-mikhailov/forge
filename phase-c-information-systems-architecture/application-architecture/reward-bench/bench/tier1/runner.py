"""Tier 1 game runner. See spec/tier1/runner.md."""
import sys
from pathlib import Path

# Make tasks/2048 importable.
_TASKS = Path(__file__).resolve().parents[2] / 'tasks/2048'
sys.path.insert(0, str(_TASKS))

from env import GameBoard


def run_game(solver, seed):
    board = GameBoard(seed=seed)
    while not board.is_terminal():
        action = solver.move(board.board)
        board.do_action(action)
    return board.score
