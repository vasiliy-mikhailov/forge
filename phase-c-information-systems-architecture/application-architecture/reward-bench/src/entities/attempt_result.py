"""Tier 1 AttemptResult entity. See src-spec/entities/src_spec_attempt_result.md.

Pure domain type — no IO, no HTTP, no external systems. The Clean
Architecture innermost layer."""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class AttemptResult:
    mean_score: float
    median_score: float
    std_score: float
    max_max_tile: int
    n_games: int
    aggregate_walltime_sec: float
    seeds: Tuple[int, ...]
