"""Stage-1 dev runner — for the OpenHands agent's ralph loop.

This is intentionally lighter than runner_tier1.py:
  - Plays 5 games (vs canonical 20) on dev seeds 1..5 (vs canonical 1000..1019)
  - Single-line summary per game + a final mean
  - No structured JSON output — designed for the agent to read in stdout

Agent invokes during ralph loop:
    bash$ python /tasks/2048/dev_runner.py /workspace/submission.py

Designed to give the agent fast feedback (~1.5s/game with the reference FSM).
The CANONICAL eval (Stage 2) uses different seeds; agent cannot overfit to dev.
"""

from __future__ import annotations

import importlib.util
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path("/env")))
try:
    from env_2048 import GameBoard
except ImportError:
    # Fallback for local dev outside the sandbox
    sys.path.insert(0, str(Path(__file__).parent))
    from env_2048_v2 import GameBoard  # type: ignore


DEV_SEEDS = (1, 2, 3, 4, 5)
DEV_TARGET = 2048
DEV_MAX_MOVES = 5_000


def _load(submission_path: str):
    spec = importlib.util.spec_from_file_location("submission", submission_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"can't load module spec from {submission_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "Solver"):
        raise AttributeError("submission must define a `Solver` class")
    return mod.Solver


def play(solver_cls, seed):
    game = GameBoard(seed=seed, target=DEV_TARGET)
    solver = solver_cls()
    moves = 0
    err = None
    while not game.is_terminal() and moves < DEV_MAX_MOVES:
        try:
            action = solver.move(game.board)
        except Exception as e:
            err = f"solver_exception: {e!r}"
            break
        if action not in ("W", "A", "S", "D"):
            err = f"invalid_action: {action!r}"
            break
        if action not in game.legal_actions():
            # Fall back; record as soft-event in stdout but don't fail
            legal = game.legal_actions()
            if not legal:
                break
            action = legal[0]
        try:
            game.do_action(action)
        except Exception as e:
            err = f"env_exception: {e!r}"
            break
        moves += 1
    return {
        "seed": seed,
        "score": game.score,
        "max_tile": game.max_tile,
        "moves": moves,
        "state": game.state,
        "err": err,
    }


def main():
    if len(sys.argv) != 2:
        print("usage: dev_runner.py <submission.py>", file=sys.stderr)
        sys.exit(2)
    sub = sys.argv[1]
    print(f"=== reward-bench dev-runner — submission: {sub} ===")
    print(f"    dev seeds: {DEV_SEEDS}, target: {DEV_TARGET}\n")

    try:
        cls = _load(sub)
    except Exception as e:
        print(f"FAIL: could not load Solver — {e!r}")
        sys.exit(1)

    t0 = time.time()
    results = []
    for s in DEV_SEEDS:
        t = time.time()
        r = play(cls, s)
        r["walltime"] = time.time() - t
        results.append(r)
        err = f"  ERR: {r['err']}" if r["err"] else ""
        print(f"  seed={s:>2}  score={r['score']:>6d}  max_tile={r['max_tile']:>4d}  "
              f"moves={r['moves']:>4d}  state={r['state']}  ({r['walltime']:.1f}s){err}")

    mean = statistics.mean(r["score"] for r in results)
    median = statistics.median(r["score"] for r in results)
    elapsed = time.time() - t0
    print(f"\n  MEAN={mean:.0f}  MEDIAN={median:.0f}  "
          f"max-tile-best={max(r['max_tile'] for r in results)}  "
          f"({elapsed:.1f}s total)")
    print(f"\nNote: Canonical eval uses different held-out seeds.")


if __name__ == "__main__":
    main()
