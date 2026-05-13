"""Tier 1 score-submission use case. See src-spec/use_cases/src_spec_score_submission.md.

Application-policy orchestrator: plays N games per the seeds list via
an injected GameEnvPort, aggregates per-game scores, returns an
AttemptResult entity. Pure application-business-rule layer: no IO,
no HTTP, no Docker."""
import statistics
import time
from typing import Callable, Iterable, Protocol

from src.entities.attempt_result import AttemptResult


class GameEnvPort(Protocol):
    """Port for the 2048 game environment.

    Adapters under src/adapters/ implement this interface against
    concrete drivers (e.g., tasks/2048/env.GameBoard).
    """

    def play_one_game(self, solver, seed: int) -> tuple:
        """Return (score: int, max_tile: int)."""
        ...


def score_submission(
    solver_factory: Callable,
    seeds: Iterable[int],
    env: GameEnvPort,
) -> AttemptResult:
    start = time.monotonic()
    seeds_tuple = tuple(seeds)
    scores = []
    max_tiles = []
    for seed in seeds_tuple:
        score, max_tile = env.play_one_game(solver_factory(), seed)
        scores.append(score)
        max_tiles.append(max_tile)
    return AttemptResult(
        mean_score=sum(scores) / len(scores),
        median_score=statistics.median(scores),
        std_score=statistics.pstdev(scores) if len(scores) > 1 else 0.0,
        max_max_tile=max(max_tiles),
        n_games=len(scores),
        aggregate_walltime_sec=time.monotonic() - start,
        seeds=seeds_tuple,
    )
