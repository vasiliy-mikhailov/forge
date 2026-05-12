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


import statistics
import time

CANONICAL_SEEDS = list(range(1000, 1020))


def run_canonical_eval(solver_factory):
    start = time.monotonic()
    results = [_run_one(solver_factory(), seed) for seed in CANONICAL_SEEDS]
    scores = [r['score'] for r in results]
    max_tiles = [r['max_tile'] for r in results]
    return {
        'mean_score': sum(scores) / len(scores),
        'median_score': statistics.median(scores),
        'std_score': statistics.pstdev(scores) if len(scores) > 1 else 0.0,
        'max_max_tile': max(max_tiles),
        'n_games': len(scores),
        'aggregate_walltime_sec': time.monotonic() - start,
    }


def _run_one(solver, seed):
    board = GameBoard(seed=seed)
    while not board.is_terminal():
        action = solver.move(board.board)
        board.do_action(action)
    return {'score': board.score, 'max_tile': board.max_tile}
