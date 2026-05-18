"""SolutionGenerator Port.

Per SOLUTION-ARCHITECTURE.md §2:

    generate :: ContextSnapshot -> SolverBody

Pure function from a fresh snapshot to a Python source string.
No memory across calls. Side effects (LLM inference) sit inside
the adapter.
"""
from __future__ import annotations

from typing import Protocol

from src.reward_bench.entities.context_snapshot import ContextSnapshot


class SolutionGenerator(Protocol):
    def generate(self, snapshot: ContextSnapshot) -> str: ...
