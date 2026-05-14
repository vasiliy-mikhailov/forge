"""Tier 1 score-submission use case.

See src-spec/tier1/use_cases/score_submission/src_spec_score_submission.md.

Application-policy orchestrator: plays N games per the seeds list via
an injected GameEnvPort, aggregates per-game scores, returns an
AttemptResult entity. Pure application-business-rule layer: no IO,
no HTTP, no Docker.

Cycle 23 (no-silent-fix): adds aggregate hard_wall_sec cap to address
the cycle-22 hang. Between games, if total elapsed exceeds
hard_wall_sec (when > 0), remaining seeds get sentinel GameResult
records with final_state='walltime_exceeded'. Per ADR 0006 layer 1.

Cycle 27 (no-silent-fix): adds per-game preemption — each
play_one_game call runs in a daemon thread with a join timeout
derived from the remaining budget. A single hanging game no longer
blocks the cap. Python daemon threads cannot be force-killed; the
thread stays alive but the orchestrator process proceeds. The Docker
tier-1 sandbox (ADR 0006 layer 2) remains the canonical fix."""
import statistics
import threading
import time
from typing import Callable, Iterable, Optional, Protocol

from src.tier1.entities.attempt_result import AttemptResult
from src.tier1.entities.game_result import GameResult


class GameEnvPort(Protocol):
    """Port for the 2048 game environment.

    Adapters under src/tier1/adapters/ implement this interface against
    concrete drivers (e.g., tasks/2048/env.GameBoard).
    """

    def play_one_game(self, solver, seed: int) -> GameResult:
        """Play one game and return a fully-populated GameResult."""
        ...


def _walltime_exceeded_sentinel(seed: int) -> GameResult:
    return GameResult(
        seed=seed, score=0, max_tile=2, moves=0,
        final_state='walltime_exceeded', walltime_sec=0.0,
    )


def _solver_error_sentinel(seed: int) -> GameResult:
    """Cycle 29: per-seed sentinel when solver_factory() raises.

    Reproduces campaign10 shape: Solver.__init__ AttributeError. The
    factory crash is uniform across seeds, but emitting one sentinel
    per seed preserves the n_games == len(seeds) artifact contract.
    See tests-spec/tier1/use_cases/score_submission/
    test_spec_when_solver_factory_raises_..."""
    return GameResult(
        seed=seed, score=0, max_tile=2, moves=0,
        final_state='solver_error', walltime_sec=0.0,
    )


def _build_solver_or_none(solver_factory):
    """Cycle 29: call solver_factory() with sentinel-on-crash.

    Returns the solver on success, None on Exception. Callers MUST
    emit _solver_error_sentinel for the current seed when this
    returns None."""
    try:
        return solver_factory()
    except Exception:
        return None


def _play_with_timeout(env, solver, seed, timeout) -> Optional[GameResult]:
    """Run env.play_one_game in a daemon thread; return the result if it
    completes within `timeout`, else None.

    Python daemon threads cannot be force-killed; on timeout the thread
    is abandoned (continues running until the process exits). For the
    bench orchestrator this is acceptable — the process is short-lived
    relative to the campaign cap."""
    captured = {'value': None, 'exc': None}

    def worker():
        try:
            captured['value'] = env.play_one_game(solver, seed)
        except BaseException as e:
            captured['exc'] = e

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout)
    if t.is_alive():
        return None
    if captured['exc'] is not None:
        raise captured['exc']
    return captured['value']


def score_submission(
    solver_factory: Callable,
    seeds: Iterable[int],
    env: GameEnvPort,
    hard_wall_sec: float = 0.0,
) -> AttemptResult:
    """Play canonical seeds; aggregate; return AttemptResult.

    `hard_wall_sec` (cycles 23 + 27 / ADR 0006 layer 1):
    - When > 0, caps the aggregate walltime BETWEEN games (cycle 23).
    - When > 0, also caps each individual game via per-game daemon
      thread + join timeout derived from remaining budget (cycle 27).
    A single hanging game no longer blocks the cap.
    Default 0 = disabled, matching the legacy unbounded behavior."""
    start = time.monotonic()
    seeds_tuple = tuple(seeds)
    games_list = []
    for seed in seeds_tuple:
        # Cycle 29: build solver with sentinel-on-crash BEFORE entering
        # play_one_game. A failing __init__ is uniform across seeds but
        # we still emit one sentinel per seed (preserves n_games shape).
        solver = _build_solver_or_none(solver_factory)
        if solver is None:
            games_list.append(_solver_error_sentinel(seed))
            continue
        if hard_wall_sec > 0:
            remaining = hard_wall_sec - (time.monotonic() - start)
            if remaining <= 0:
                # Aggregate cap exhausted; sentinel for this and the rest.
                games_list.append(_walltime_exceeded_sentinel(seed))
                continue
            # Cycle 27: per-game cap = remaining aggregate budget.
            game = _play_with_timeout(env, solver, seed, timeout=remaining)
            if game is None:
                # This game alone burned the rest of the budget.
                games_list.append(_walltime_exceeded_sentinel(seed))
                continue
            games_list.append(game)
        else:
            games_list.append(env.play_one_game(solver, seed))
    games = tuple(games_list)
    scores = [g.score for g in games]
    max_tiles = [g.max_tile for g in games]
    return AttemptResult(
        mean_score=sum(scores) / len(scores),
        median_score=statistics.median(scores),
        std_score=statistics.pstdev(scores) if len(scores) > 1 else 0.0,
        max_max_tile=max(max_tiles),
        n_games=len(scores),
        aggregate_walltime_sec=time.monotonic() - start,
        games=games,
        hard_wall_sec=hard_wall_sec,
        stagnated_any=any(g.final_state == 'stagnated' for g in games),
        walltime_exceeded=any(g.final_state == 'walltime_exceeded' for g in games),
    )
