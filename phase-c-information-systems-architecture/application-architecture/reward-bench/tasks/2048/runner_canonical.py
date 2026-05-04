"""tier-1 runner — runs INSIDE the Docker sandbox.

Loads the submitted Solver from /workspace/submission.py, plays N games of
2048 (deterministic seed sequence), writes structured result.json + events.jsonl.

Inputs (env vars):
    REWARD_BENCH_NUM_GAMES   default 20
    REWARD_BENCH_SEED_BASE   default 0
    REWARD_BENCH_TARGET      default 2048
    REWARD_BENCH_MAX_MOVES   default 10000

Output paths (matched to /reports mount inside the container):
    /reports/result.json
    /reports/events.jsonl
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import traceback
from pathlib import Path

# /env is the read-only mount where env_2048 lives
sys.path.insert(0, "/env")
from env_2048 import GameBoard  # type: ignore


def _load_submission(submission_path: str):
    spec = importlib.util.spec_from_file_location("submission", submission_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"can't load module spec from {submission_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "Solver"):
        raise AttributeError("submission must define a `Solver` class")
    return mod.Solver


def _play_one(solver_class, seed: int, target: int, max_moves: int, events_fp):
    game = GameBoard(seed=seed, target=target)
    solver = solver_class()
    moves = 0
    final_state = "max_moves"
    while not game.is_terminal() and moves < max_moves:
        # Pass an immutable copy to the solver
        board = game.board
        try:
            action = solver.move(board)
        except Exception as e:
            events_fp.write(json.dumps({
                "seed": seed, "move": moves, "event": "solver_exception",
                "exc": repr(e), "traceback": traceback.format_exc(),
            }) + "\n")
            final_state = "solver_error"
            break

        if action not in ("W", "A", "S", "D"):
            events_fp.write(json.dumps({
                "seed": seed, "move": moves, "event": "invalid_action",
                "action": repr(action),
            }) + "\n")
            final_state = "invalid_action"
            break

        legal = game.legal_actions()
        if action not in legal:
            # Solver picked an action that wouldn't change the board.
            # Fall back to first legal in canonical order; record event.
            events_fp.write(json.dumps({
                "seed": seed, "move": moves, "event": "illegal_action_fallback",
                "tried": action, "legal": legal, "fallback": legal[0] if legal else None,
            }) + "\n")
            if not legal:
                break
            action = legal[0]

        try:
            game.do_action(action)
        except Exception as e:
            events_fp.write(json.dumps({
                "seed": seed, "move": moves, "event": "env_exception",
                "exc": repr(e),
            }) + "\n")
            break

        moves += 1
        # Compact step trace — keep events.jsonl readable
        if moves % 10 == 0 or game.is_terminal():
            events_fp.write(json.dumps({
                "seed": seed, "move": moves, "event": "checkpoint",
                "score": game.score, "max_tile": game.max_tile, "state": game.state,
            }) + "\n")

    if game.state in ("won", "lost"):
        final_state = game.state
    return {
        "seed": seed,
        "score": game.score,
        "max_tile": game.max_tile,
        "moves": moves,
        "final_state": final_state,
    }


def main():
    submission_path = os.environ.get("REWARD_BENCH_SUBMISSION", "/workspace/submission.py")
    n_games = int(os.environ.get("REWARD_BENCH_NUM_GAMES", "20"))
    seed_base = int(os.environ.get("REWARD_BENCH_SEED_BASE", "0"))
    target = int(os.environ.get("REWARD_BENCH_TARGET", "2048"))
    max_moves = int(os.environ.get("REWARD_BENCH_MAX_MOVES", "10000"))

    reports_dir = Path(os.environ.get("REWARD_BENCH_REPORTS", "/reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    result_path = reports_dir / "result.json"
    events_path = reports_dir / "events.jsonl"

    t0 = time.time()
    try:
        solver_class = _load_submission(submission_path)
    except Exception as e:
        result_path.write_text(json.dumps({
            "error": "submission_load_failed",
            "exc": repr(e),
            "traceback": traceback.format_exc(),
            "walltime_sec": time.time() - t0,
        }, indent=2))
        return 1

    games = []
    with open(events_path, "w") as events_fp:
        for i in range(n_games):
            t_game = time.time()
            res = _play_one(solver_class, seed=seed_base + i, target=target,
                            max_moves=max_moves, events_fp=events_fp)
            res["walltime_sec"] = time.time() - t_game
            games.append(res)

    scores = [g["score"] for g in games]
    max_tiles = [g["max_tile"] for g in games]
    n = len(scores)

    summary = {
        "games": games,
        "n_games": n,
        "mean_score": sum(scores) / n if n else 0.0,
        "median_score": sorted(scores)[n // 2] if n else 0,
        "min_score": min(scores) if scores else 0,
        "max_score": max(scores) if scores else 0,
        "max_max_tile": max(max_tiles) if max_tiles else 0,
        "aggregate_walltime_sec": time.time() - t0,
    }
    result_path.write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
