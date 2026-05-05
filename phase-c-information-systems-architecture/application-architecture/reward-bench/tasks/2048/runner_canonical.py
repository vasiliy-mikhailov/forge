"""tier-1 runner — runs INSIDE the Docker sandbox.

Loads the submitted Solver from /workspace/submission.py, plays N games of
2048 (deterministic seed sequence), writes structured result.json + events.jsonl.

Inputs (env vars):
    REWARD_BENCH_NUM_GAMES        default 20
    REWARD_BENCH_SEED_BASE        default 0
    REWARD_BENCH_TARGET           default 2048
    REWARD_BENCH_MAX_MOVES        default 10000
    REWARD_BENCH_STAGNATION_SEC   default 60. Per-game stagnation detector:
                                  if neither game.score nor game.max_tile has
                                  increased for this many seconds of wall time,
                                  the game ends with final_state="stagnated".
                                  This replaces the previous hard 5-min wall
                                  budget; it works for any tier because it's
                                  wall-time-based regardless of decision
                                  latency (a tier-1 FSM with millisecond
                                  decisions or a tier-2 LangGraph with 2 s
                                  decisions are both bounded by the same rule).
    REWARD_BENCH_HARD_WALL_SEC    default 0 (disabled). Optional outer
                                  runaway-protection cap across the whole 20-
                                  game eval. Set to a positive number to keep
                                  the previous "kill the run after N seconds"
                                  behaviour as a safety net.

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


def _play_one(solver_class, seed: int, target: int, max_moves: int,
              events_fp, stagnation_sec: float = 60.0,
              hard_deadline: float | None = None):
    """Play one game.

    Stagnation rule: if neither game.score nor game.max_tile has changed for
    `stagnation_sec` seconds of wall time, the game ends with
    final_state="stagnated" — the score accumulated so far is kept.

    Optional `hard_deadline` (monotonic clock seconds) is an outer
    runaway-protection cap across the whole eval; if it fires mid-game the
    game ends with final_state="walltime_exceeded" (kept for backward
    compatibility with REWARD_BENCH_HARD_WALL_SEC; default disabled).
    """
    game = GameBoard(seed=seed, target=target)
    solver = solver_class()
    moves = 0
    final_state = "max_moves"
    last_progress_t = time.monotonic()
    last_progress_score = game.score
    last_progress_tile = game.max_tile
    while not game.is_terminal() and moves < max_moves:
        now = time.monotonic()
        if hard_deadline is not None and now >= hard_deadline:
            events_fp.write(json.dumps({
                "seed": seed, "move": moves, "event": "walltime_exceeded_midgame",
                "score": game.score, "max_tile": game.max_tile,
            }) + "\n")
            final_state = "walltime_exceeded"
            break
        if (now - last_progress_t) >= stagnation_sec:
            events_fp.write(json.dumps({
                "seed": seed, "move": moves, "event": "stagnated",
                "score": game.score, "max_tile": game.max_tile,
                "secs_since_progress": now - last_progress_t,
            }) + "\n")
            final_state = "stagnated"
            break
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
        # Track progress for stagnation detector — score or max-tile increase
        # resets the stagnation clock.
        if game.score > last_progress_score or game.max_tile > last_progress_tile:
            last_progress_t = time.monotonic()
            last_progress_score = game.score
            last_progress_tile = game.max_tile
        # Compact step trace — keep events.jsonl readable
        if moves % 10 == 0 or game.is_terminal():
            events_fp.write(json.dumps({
                "seed": seed, "move": moves, "event": "checkpoint",
                "score": game.score, "max_tile": game.max_tile, "state": game.state,
            }) + "\n")

    if game.state in ("won", "lost") and final_state not in ("walltime_exceeded", "stagnated"):
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
    stagnation_sec = float(os.environ.get("REWARD_BENCH_STAGNATION_SEC", "60"))
    hard_wall_sec = float(os.environ.get("REWARD_BENCH_HARD_WALL_SEC", "0"))

    reports_dir = Path(os.environ.get("REWARD_BENCH_REPORTS", "/reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    result_path = reports_dir / "result.json"
    events_path = reports_dir / "events.jsonl"

    t0 = time.time()
    mono0 = time.monotonic()
    hard_deadline = mono0 + hard_wall_sec if hard_wall_sec > 0 else None
    try:
        solver_class = _load_submission(submission_path)
    except Exception as e:
        result_path.write_text(json.dumps({
            "error": "submission_load_failed",
            "exc": repr(e),
            "traceback": traceback.format_exc(),
            "walltime_sec": time.time() - t0,
            "stagnation_sec": stagnation_sec,
            "hard_wall_sec": hard_wall_sec,
        }, indent=2))
        return 1

    games = []
    walltime_exceeded = False
    stagnated_any = False
    with open(events_path, "w") as events_fp:
        for i in range(n_games):
            seed = seed_base + i
            if hard_deadline is not None and time.monotonic() >= hard_deadline:
                # Outer runaway cap kicked in. Mark remaining games as skipped.
                events_fp.write(json.dumps({
                    "seed": seed, "event": "walltime_exceeded_skip",
                }) + "\n")
                games.append({
                    "seed": seed,
                    "score": 0,
                    "max_tile": 0,
                    "moves": 0,
                    "final_state": "walltime_exceeded",
                    "walltime_sec": 0.0,
                })
                walltime_exceeded = True
                continue
            t_game = time.time()
            res = _play_one(solver_class, seed=seed, target=target,
                            max_moves=max_moves, events_fp=events_fp,
                            stagnation_sec=stagnation_sec,
                            hard_deadline=hard_deadline)
            res["walltime_sec"] = time.time() - t_game
            games.append(res)
            if res["final_state"] == "walltime_exceeded":
                walltime_exceeded = True
            if res["final_state"] == "stagnated":
                stagnated_any = True

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
        "stagnation_sec": stagnation_sec,
        "hard_wall_sec": hard_wall_sec,
        "walltime_exceeded": walltime_exceeded,
        "stagnated_any": stagnated_any,
    }
    result_path.write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
