"""FakeOrchestrator — scripted Orchestrator Port test double per ADR-0018."""
from __future__ import annotations

from typing import Iterable

from src.tier1.entities.submission import Submission


class FakeOrchestrator:
    def __init__(self, submissions):
        self._submissions = tuple(submissions)

    def orchestrate(self, env, cfg) -> Iterable[Submission]:
        return self._submissions
