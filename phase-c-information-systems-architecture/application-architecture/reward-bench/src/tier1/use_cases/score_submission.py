"""Tier 1 score-submission use case.

See src-spec/tier1/use_cases/score_submission/src_spec_score_submission.md.

Application-policy orchestrator: plays N games per the seeds list via
an injected GameEnvPort, aggregates per-game scores, returns an
AttemptResult entity. Pure application-business-rule layer: no IO,
no HTTP, no Docker.

Cycle 23 (no-silent-fix): adds aggregate hard_wall_sec cap to address
the cycle-22 hang. Between games, if total elapsed exceeds
hard_wall_sec (when > 0), remaining seeds get sentinel GameResult
records with final_state='walltime_exceeded'. Per ADR 0006 layer 1."""
import statistics
import time
from typing import Callable, Iterable, Protocol

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


def score_submission(
    solver_factory: Callable,
    seeds: Iterable[int],
    env: GameEnvPort,
    hard_wall_sec: float = 0.0,
) -> AttemptResult:
    """Play canonical seeds; aggregate; return AttemptResult.

    `hard_wall_sec`: per ADR 0006 layer 1, when > 0 caps the aggregate
    walltime; remaining seeds after the cap fires are filled with
    final_state='walltime_exceeded' sentinels. Default 0 = disabled,
    matching the legacy behavior."""
    start = time.monotonic()
    seeds_tuple = tuple(seeds)
    games_list = []
    for seed in seeds_tuple:
        if hard_wall_sec > 0 and (time.monotonic() - start) > hard_wall_sec:
            # Aggregate cap exceeded; emit sentinel for this and remaining seeds.
            games_list.append(GameResult(
                seed=seed, score=0, max_tile=2, moves=0,
                final_state='walltime_exceeded', walltime_sec=0.0,
            ))
            continue
        games_list.append(env.play_one_game(solver_factory(), seed))
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
