"""Tier 1 AttemptResult entity. Pure domain type — no IO, no HTTP."""
from dataclasses import dataclass, field
from typing import Tuple

from src.tier1.entities.game_result import GameResult


@dataclass(frozen=True)
class AttemptResult:
    mean_score: float
    median_score: float
    std_score: float
    max_max_tile: int
    n_games: int
    aggregate_walltime_sec: float
    games: Tuple[GameResult, ...] = field(default_factory=tuple)
    stagnation_sec: float = 60.0
    hard_wall_sec: float = 0.0
    stagnated_any: bool = False
    walltime_exceeded: bool = False
    solver_protocol_valid: bool = True
    best_dev_mean: float | None = None
                                         # best dev_mean observed during the
                                         # agent loop (from execute_submission).
                                         # Used as the smoke success criterion.
