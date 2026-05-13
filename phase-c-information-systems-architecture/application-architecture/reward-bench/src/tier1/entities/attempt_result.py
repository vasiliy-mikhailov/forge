"""Tier 1 AttemptResult entity. See src-spec/tier1/entities/attempt_result/.

Pure domain type — no IO, no HTTP, no external systems. The Clean
Architecture innermost layer."""
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
