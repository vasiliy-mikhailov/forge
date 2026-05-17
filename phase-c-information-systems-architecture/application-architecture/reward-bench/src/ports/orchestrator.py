"""Orchestrator Port.

Per SOLUTION-ARCHITECTURE.md §7:

    orchestrate :: Env -> BenchConfig -> [Submission]

The seam both strategies (ralph single-context, subagent-per-iter)
implement. Bench composes against this Protocol; adapter swaps
(OpenHands, homegrown) do not touch bench-side code.
"""
from __future__ import annotations

from typing import Iterable, Protocol

from src.tier1.entities.submission import Submission


class Orchestrator(Protocol):
    def orchestrate(self, env, cfg) -> Iterable[Submission]: ...
