"""Tier 1 scorer. See src-spec/tier1/src_spec_when_solver_plays_*.md."""
import statistics
import sys
import time
from pathlib import Path


_TASKS = Path(__file__).resolve().parents[2] / 'tasks/2048'
if str(_TASKS) not in sys.path:
    sys.path.insert(0, str(_TASKS))

from env import GameBoard  # noqa: E402


CANONICAL_SEEDS = list(range(1000, 1020))


def _play(solver, seed):
    """Play one game; return (score, max_tile)."""
    board = GameBoard(seed=seed)
    while not board.is_terminal():
        action = solver.move(board.board)
        board.do_action(action)
    return board.score, board.max_tile


def score_one_game(solver, seed):
    score, _ = _play(solver, seed)
    return score


def run_canonical_eval(solver_factory):
    start = time.monotonic()
    scores = []
    max_tiles = []
    for seed in CANONICAL_SEEDS:
        s, mt = _play(solver_factory(), seed)
        scores.append(s)
        max_tiles.append(mt)
    return {
        'mean_score': sum(scores) / len(scores),
        'median_score': statistics.median(scores),
        'std_score': statistics.pstdev(scores) if len(scores) > 1 else 0.0,
        'max_max_tile': max(max_tiles),
        'n_games': len(scores),
        'aggregate_walltime_sec': time.monotonic() - start,
        'seeds': list(CANONICAL_SEEDS),
    }
