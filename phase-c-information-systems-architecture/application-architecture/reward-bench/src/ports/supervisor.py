"""SupervisorPort — abstraction over plateau-detection per ADR 0005.

Adapters under src/reward_bench/adapters/ implement this interface;
the canonical adapter is LlmSupervisor (delegates to the bench LLM
under test per ADR 0001). The trivial NullSupervisor lives at
src/reward_bench/adapters/null_supervisor.py and serves as the
default when no supervisor is configured.

Relocated from src.reward_bench.use_cases.supervisor_port in
cycle 115 to comply with ADR 0018's src/ports/<name>.py convention.
"""
from typing import Protocol, Tuple, runtime_checkable

from src.reward_bench.entities.supervisor_decision import SupervisorDecision


# A Sample is the four-signal record ADR 0005 calls out as the
# supervisor's input: (iter_no, mean_score, max_tile, walltime_sec).
# Kept as a plain tuple to avoid an extra entity for one row.
Sample = Tuple[int, float, int, float]


@runtime_checkable
class SupervisorPort(Protocol):
    """Judges plateau from recent dev_runner samples per ADR 0005."""

    def judge(self, sweep: Tuple[Sample, ...]) -> SupervisorDecision:
        """Inspect samples and return a frozen SupervisorDecision."""
        ...
