"""NullSupervisor — trivial SupervisorPort adapter that never recommends stop.

The default supervisor when no live LLM-based one is configured.
Also the test anchor for SupervisorPort runtime-checkable conformance.

Relocated from src.reward_bench.use_cases.supervisor_port in
cycle 115.
"""
from typing import Tuple

from src.ports.supervisor import Sample
from src.reward_bench.entities.supervisor_decision import SupervisorDecision


class NullSupervisor:
    """Always says 'keep going'. Default when supervisor_every_k == 0."""

    def judge(self, sweep: Tuple[Sample, ...]) -> SupervisorDecision:
        return SupervisorDecision(
            plateau=False,
            stop_recommended=False,
            reasoning='null supervisor: never stop',
        )
