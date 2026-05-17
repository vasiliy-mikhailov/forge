"""Tier 1 score-submission use case.

Application-policy orchestrator: plays N games per the seeds list via
an injected GameEnvPort, aggregates per-game scores, returns an
AttemptResult entity. Pure application-business-rule layer: no IO,
no HTTP, no Docker.

Applies an aggregate hard_wall_sec cap between games; per-game
preemption via daemon-thread join timeout."""
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
    """Per-seed sentinel when solver_factory() raises (one per seed
    so n_games == len(seeds) is preserved)."""
    return GameResult(
        seed=seed, score=0, max_tile=2, moves=0,
        final_state='solver_error', walltime_sec=0.0,
    )


def _build_solver_or_none(solver_factory):
    """Call solver_factory() with sentinel-on-crash. Returns the
    solver on success, None on Exception."""
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
        # Redirect stdout/stderr around the Solver call so model-emitted
        # print() inside move() doesn't flood the bench log.
        import io as _io
        import contextlib as _ctx
        _sink_out = _io.StringIO()
        _sink_err = _io.StringIO()
        try:
            with _ctx.redirect_stdout(_sink_out), _ctx.redirect_stderr(_sink_err):
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

    `hard_wall_sec`:
    - When > 0, caps the aggregate walltime BETWEEN games.
    - When > 0, also caps each individual game via per-game daemon
      thread + join timeout derived from remaining budget.
    Default 0 = disabled."""
    start = time.monotonic()
    seeds_tuple = tuple(seeds)
    games_list = []
    for seed in seeds_tuple:
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
