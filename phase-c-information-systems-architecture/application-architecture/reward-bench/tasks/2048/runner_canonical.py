"""tier-1 runner — runs INSIDE the Docker sandbox.

Parallelises the N-seed eval using `multiprocessing.Pool(
processes=multiprocessing.cpu_count())`. Container sees only the
cgroup-allocated cores (Docker `--cpus=N` sets the quota).

Loads /workspace/submission.py, plays N games of 2048 (deterministic
seed sequence), writes /reports/result.json + /reports/events.jsonl.

Inputs (env vars):
    REWARD_BENCH_NUM_GAMES         default 20
    REWARD_BENCH_SEED_BASE         default 0
    REWARD_BENCH_TARGET            default 2048
    REWARD_BENCH_MAX_MOVES         default 10000
    REWARD_BENCH_STAGNATION_SEC    default 60
    REWARD_BENCH_HARD_WALL_SEC     default 0 (disabled)
    REWARD_BENCH_MOVES_STAGNATION  default 100 (moves-wise stagnation)
"""
from __future__ import annotations

import importlib.util
import json
import multiprocessing
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, "/env")
from env_2048 import GameBoard  # type: ignore


# Moves-wise stagnation: if MOVES_STAGNATION consecutive moves pass
# without score or max_tile increase, mark the game `stagnated`.
MOVES_STAGNATION = int(os.environ.get("REWARD_BENCH_MOVES_STAGNATION", "100"))


def _load_submission(submission_path: str):
    spec = importlib.util.spec_from_file_location("submission", submission_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"can't load module spec from {submission_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "Solver"):
        raise AttributeError("submission must define a `Solver` class")
    return mod.Solver


def _play_one_collect_events(args):
    """Run one game in a worker process; returns (game_result_dict, list_of_event_dicts).

    hard_deadline_wall is absolute time.time() seconds (wall time is
    cross-process portable; monotonic isn't).
    """
    (submission_path, seed, target, max_moves,
     stagnation_sec, hard_deadline_wall) = args

    events: list[dict] = []
    try:
        solver_class = _load_submission(submission_path)
    except Exception as e:
        return ({
            "seed": seed,
            "score": 0,
            "max_tile": 0,
            "moves": 0,
            "final_state": "solver_error",
            "walltime_sec": 0.0,
            "error": f"{type(e).__name__}: {e}",
        }, events)

    try:
        solver = solver_class()
    except Exception as e:
        return ({
            "seed": seed,
            "score": 0,
            "max_tile": 0,
            "moves": 0,
            "final_state": "solver_error",
            "walltime_sec": 0.0,
            "error": f"Solver.__init__: {type(e).__name__}: {e}",
        }, events)

    game = GameBoard(seed=seed, target=target)
    moves = 0
    final_state = "max_moves"
    last_progress_t = time.monotonic()
    last_progress_move = 0
    last_progress_score = game.score
    last_progress_tile = game.max_tile
    t_game_start = time.time()

    while not game.is_terminal() and moves < max_moves:
        now_mono = time.monotonic()
        now_wall = time.time()
        if hard_deadline_wall is not None and now_wall >= hard_deadline_wall:
            events.append({
                "seed": seed, "move": moves, "event": "walltime_exceeded_midgame",
                "score": game.score, "max_tile": game.max_tile,
            })
            final_state = "walltime_exceeded"
            break
        if (now_mono - last_progress_t) >= stagnation_sec:
            events.append({
                "seed": seed, "move": moves, "event": "stagnated",
                "score": game.score, "max_tile": game.max_tile,
                "secs_since_progress": now_mono - last_progress_t,
            })
            final_state = "stagnated"
            break
        if (moves - last_progress_move) >= MOVES_STAGNATION:
            events.append({
                "seed": seed, "move": moves, "event": "stagnated_moves",
                "score": game.score, "max_tile": game.max_tile,
                "moves_since_progress": moves - last_progress_move,
            })
            final_state = "stagnated"
            break
        board = game.board
        try:
            action = solver.move(board)
        except Exception as e:
            events.append({
                "seed": seed, "move": moves, "event": "solver_raised",
                "error": f"{type(e).__name__}: {e}",
            })
            final_state = "solver_error"
            break
        if not isinstance(action, str) or action not in ("W", "A", "S", "D"):
            events.append({
                "seed": seed, "move": moves, "event": "invalid_action",
                "action": repr(action),
            })
            final_state = "invalid_action"
            break
        game.do_action(action)
        moves += 1
        if game.score > last_progress_score or game.max_tile > last_progress_tile:
            last_progress_t = time.monotonic()
            last_progress_move = moves
            last_progress_score = game.score
            last_progress_tile = game.max_tile
        if moves % 10 == 0 or game.is_terminal():
            events.append({
                "seed": seed, "move": moves, "event": "checkpoint",
                "score": game.score, "max_tile": game.max_tile,
                "state": game.state,
            })

    if game.state in ("won", "lost") and final_state not in ("walltime_exceeded", "stagnated", "solver_error", "invalid_action"):
        final_state = game.state

    return ({
        "seed": seed,
        "score": game.score,
        "max_tile": game.max_tile,
        "moves": moves,
        "final_state": final_state,
        "walltime_sec": time.time() - t_game_start,
    }, events)


def main():
    submission_path = os.environ.get("REWARD_BENCH_SUBMISSION", "/workspace/submission.py")
    n_games = int(os.environ.get("REWARD_BENCH_NUM_GAMES", "20"))
    seed_base = int(os.environ.get("REWARD_BENCH_SEED_BASE", "0"))
    target = int(os.environ.get("REWARD_BENCH_TARGET", "2048"))
    max_moves = int(os.environ.get("REWARD_BENCH_MAX_MOVES", "10000"))
    stagnation_sec = float(os.environ.get("REWARD_BENCH_STAGNATION_SEC", "60"))
    hard_wall_sec = float(os.environ.get("REWARD_BENCH_HARD_WALL_SEC", "0"))

    reports_dir = Path(os.environ.get("REWARD_BENCH_REPORTS", "/reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    result_path = reports_dir / "result.json"
    events_path = reports_dir / "events.jsonl"

    t0_wall = time.time()
    hard_deadline_wall = t0_wall + hard_wall_sec if hard_wall_sec > 0 else None

    try:
        _load_submission(submission_path)
    except Exception as e:
        result_path.write_text(json.dumps({
            "error": "submission_load_failed",
            "exc": repr(e),
            "traceback": traceback.format_exc(),
            "walltime_sec": time.time() - t0_wall,
            "stagnation_sec": stagnation_sec,
            "hard_wall_sec": hard_wall_sec,
        }, indent=2))
        return 1

    n_workers = max(1, multiprocessing.cpu_count())

    # Build per-seed work items.
    work = [
        (submission_path, seed_base + i, target, max_moves,
         stagnation_sec, hard_deadline_wall)
        for i in range(n_games)
    ]

    games: list[dict] = []
    events: list[dict] = []
    walltime_exceeded = False
    stagnated_any = False

    with multiprocessing.Pool(processes=n_workers) as pool:
        for game, ev in pool.imap_unordered(_play_one_collect_events, work):
            games.append(game)
            events.extend(ev)
            if game["final_state"] == "walltime_exceeded":
                walltime_exceeded = True
            if game["final_state"] == "stagnated":
                stagnated_any = True
            if hard_deadline_wall is not None and time.time() >= hard_deadline_wall:
                pool.terminate()
                walltime_exceeded = True
                break

    games.sort(key=lambda g: g["seed"])
    events.sort(key=lambda e: (e.get("seed", 0), e.get("move", 0)))

    # Backfill missing seeds with walltime_exceeded sentinels.
    completed_seeds = {g["seed"] for g in games}
    for i in range(n_games):
        seed = seed_base + i
        if seed not in completed_seeds:
            games.append({
                "seed": seed, "score": 0, "max_tile": 0, "moves": 0,
                "final_state": "walltime_exceeded", "walltime_sec": 0.0,
            })
            walltime_exceeded = True
    games.sort(key=lambda g: g["seed"])

    with open(events_path, "w") as events_fp:
        for ev in events:
            events_fp.write(json.dumps(ev) + "\n")

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
        "aggregate_walltime_sec": time.time() - t0_wall,
        "stagnation_sec": stagnation_sec,
        "hard_wall_sec": hard_wall_sec,
        "walltime_exceeded": walltime_exceeded,
        "stagnated_any": stagnated_any,
        "n_workers": n_workers,
    }
    result_path.write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
