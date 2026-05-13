"""Tier 1 score-submission use case.

See src-spec/tier1/use_cases/score_submission/src_spec_score_submission.md.

Application-policy orchestrator: plays N games per the seeds list via
an injected GameEnvPort, aggregates per-game scores, returns an
AttemptResult entity. Pure application-business-rule layer: no IO,
no HTTP, no Docker."""
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
) -> AttemptResult:
    start = time.monotonic()
    seeds_tuple = tuple(seeds)
    games = tuple(env.play_one_game(solver_factory(), seed)
                  for seed in seeds_tuple)
    scores = [g.score for g in games]
    max_tiles = [g.max_tile for g in games]
    return AttemptResult(
        mean_score=sum(scores) / len(scores),
        median_score=statistics.median(scores),
        std_score=statistics.pstdev(scores) if len(scores) > 1 else 0.0,
        max_max_tile=max(max_tiles),
        n_games=len(scores),
        aggregate_walltime_sec=time.monotonic() - start,
        seeds=seeds_tuple,
        games=games,
        stagnated_any=any(g.final_state == 'stagnated' for g in games),
        walltime_exceeded=any(g.final_state == 'walltime_exceeded' for g in games),
    )
