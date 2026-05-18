"""§2 `ContextSnapshot` — what the SolutionGenerator receives per iter.

The orchestrator builds one of these from cumulative state each
iter. Its deliberation tokens die with its context; this snapshot
is the only state that survives.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.tier1.entities.submission import Submission


@dataclass(frozen=True)
class ContextSnapshot:
    env_spec: str
    best_so_far: Submission
    history_digest: tuple[Submission, ...]
    iters_remaining: int
    time_remaining_sec: float
    budget_sec_per_seed: float
