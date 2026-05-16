"""Cycle 109 / ADR 0018: InProcessCanonicalScorer adapter.

Wraps the in-process `score_submission` use-case (cycle 23/27 daemon-
thread timeout, Layer 1 per ADR 0006) as a `CanonicalScorerPort`.

Production use is typically `DockerCanonicalScorer` (Layer 2); this
adapter exists for parity, for offline benchmarking when Docker isn't
available, and to give the canonical-scorer port a real (not just
Fake) alternative.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.ports.canonical_scorer import CanonicalScorerPort
from src.tier1.entities.attempt_result import AttemptResult


class InProcessCanonicalScorer(CanonicalScorerPort):
    """Wraps `src.tier1.use_cases.score_submission.score_submission` as
    a `CanonicalScorerPort`.

    Loads the submission module from `submission_path`, instantiates
    `Solver`, plays the seeds via the cycle-23/27 daemon-thread harness,
    returns an `AttemptResult`. Per ADR 0006 Layer 1; isolation is
    best-effort (Python thread, not OS process).
    """

    def __init__(self, env=None):
        # Default env: tier-1's GameBoard2048Adapter. Tests can inject
        # a synthetic env.
        if env is None:
            from src.tier1.adapters.game_board_2048 import GameBoard2048Adapter
            env = GameBoard2048Adapter()
        self._env = env

    def score(
        self,
        submission_path,
        seeds: Iterable[int],
        *,
        hard_wall_sec: float = 0.0,
        reports_root=None,
    ) -> AttemptResult:
        from src.tier1.harness import load_submission
        from src.tier1.use_cases.score_submission import score_submission

        module = load_submission(Path(submission_path))
        return score_submission(
            module.Solver, list(seeds), self._env,
            hard_wall_sec=hard_wall_sec,
        )
