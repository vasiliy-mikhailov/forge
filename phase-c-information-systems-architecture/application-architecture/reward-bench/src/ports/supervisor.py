"""SupervisorPort — abstraction over plateau-detection."""
from typing import Protocol, Tuple, runtime_checkable

from src.reward_bench.entities.supervisor_decision import SupervisorDecision


Sample = Tuple[int, float, int, float]


@runtime_checkable
class SupervisorPort(Protocol):
    """Judges plateau from recent dev_runner samples."""

    def judge(self, sweep: Tuple[Sample, ...]) -> SupervisorDecision:
        """Inspect samples and return a frozen SupervisorDecision."""
        ...
