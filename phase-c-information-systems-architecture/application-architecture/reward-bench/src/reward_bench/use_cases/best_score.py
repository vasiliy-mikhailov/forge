"""§7 dominance-test fitness primitive.

    best_score env cfg t =
        max { score env s
            | s in orchestrate env cfg,
              submission_walltime s <= t }

Pure reduction: filter by walltime budget, then argmax-by-score.
"""
from __future__ import annotations

from typing import Iterable

from src.tier1.entities.submission import Submission


def best_score(
    submissions: Iterable[Submission],
    walltime_budget_sec: float,
) -> float:
    return max(
        s.score for s in submissions if s.walltime_sec <= walltime_budget_sec
    )
