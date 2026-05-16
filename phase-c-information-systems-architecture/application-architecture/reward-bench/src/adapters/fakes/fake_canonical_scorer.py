"""Cycle 109 / ADR 0018: FakeCanonicalScorer adapter.

Returns scripted AttemptResults; records every call onto `.calls`.
Used by the conftest autouse fixture as the default-bound canonical
scorer so tests reaching main() don't spawn Docker.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.ports.canonical_scorer import CanonicalScorerPort
from src.tier1.entities.attempt_result import AttemptResult


class FakeCanonicalScorer(CanonicalScorerPort):
    """Scripted in-memory `CanonicalScorerPort`."""

    def __init__(
        self,
        script: tuple[AttemptResult, ...] | list[AttemptResult] | None = None,
        *,
        default_result: AttemptResult | None = None,
    ):
        self._script = tuple(script) if script else ()
        self._default = default_result
        self._i = 0
        self.calls: list[dict] = []

    def score(
        self,
        submission_path,
        seeds: Iterable[int],
        *,
        hard_wall_sec: float = 0.0,
        reports_root=None,
    ) -> AttemptResult:
        self.calls.append({
            "submission_path": str(submission_path),
            "seeds": tuple(seeds),
            "hard_wall_sec": hard_wall_sec,
            "reports_root": str(reports_root) if reports_root else None,
        })
        if self._i < len(self._script):
            r = self._script[self._i]
            self._i += 1
            return r
        if self._default is not None:
            return self._default
        # Sane empty-ish default: no games scored.
        return AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=0, n_games=0, aggregate_walltime_sec=0.0,
            games=(), hard_wall_sec=hard_wall_sec,
            stagnated_any=False, walltime_exceeded=False,
        )
