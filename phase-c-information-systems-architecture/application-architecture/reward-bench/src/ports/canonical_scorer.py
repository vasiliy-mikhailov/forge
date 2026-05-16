"""Cycle 109 / ADR 0018: CanonicalScorerPort.

A CanonicalScorerPort plays a submission against a set of seeds and
returns the aggregated AttemptResult. Production binding spawns a
reward-bench-tier1 Docker container (Layer 2 per ADR 0006). Test
binding returns scripted results in-memory.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Protocol

from src.tier1.entities.attempt_result import AttemptResult


class CanonicalScorerPort(Protocol):
    """Plays a submission against seeds; returns AttemptResult.

    Implementations MUST NOT raise on hostile submissions — bad code
    surfaces as protocol_violations / per-seed sentinel `final_state`
    on the returned AttemptResult.
    """

    def score(
        self,
        submission_path: str | Path,
        seeds: Iterable[int],
        *,
        hard_wall_sec: float = 0.0,
        reports_root: str | Path | None = None,
    ) -> AttemptResult: ...
