"""FakeSolutionGenerator — scripted SolutionGenerator Port test double."""
from __future__ import annotations


class FakeSolutionGenerator:
    def __init__(self, body: str):
        self._body = body

    def generate(self, snapshot) -> str:
        return self._body
