"""`best_submission` — pure argmax-by-score over an iterable of Submissions.

Per SOLUTION-ARCHITECTURE.md §7:

    bench env cfg = argmaxBy (.score) (orchestrate env cfg)

The bench composes this primitive with an `Orchestrator` to define
the top-level fitness target.
"""
from __future__ import annotations

from typing import Iterable

from src.tier1.entities.submission import Submission


def best_submission(submissions: Iterable[Submission]) -> Submission:
    return max(submissions, key=lambda s: s.score)
