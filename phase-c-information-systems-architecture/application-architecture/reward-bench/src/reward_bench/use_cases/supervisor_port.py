"""SupervisorPort: application-layer abstraction over ADR 0005's
plateau-detection step.

See src-spec/reward_bench/use_cases/supervisor_port/.

Adapters under src/reward_bench/adapters/ implement this interface.
The canonical adapter is LlmSupervisor (cycle 32) which delegates
to the bench LLM under test per ADR 0001. This file also ships
NullSupervisor — the trivial "never stop" default that lets cycle 33
wire agent_loop to a supervisor without changing behavior."""
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


class NullSupervisor:
    """Trivial implementation: always says 'keep going'.

    Default for agent_loop when no supervisor is configured; also
    the test anchor for the SupervisorPort protocol."""

    def judge(self, sweep: Tuple[Sample, ...]) -> SupervisorDecision:
        return SupervisorDecision(
            plateau=False,
            stop_recommended=False,
            reasoning='null supervisor: never stop',
        )
