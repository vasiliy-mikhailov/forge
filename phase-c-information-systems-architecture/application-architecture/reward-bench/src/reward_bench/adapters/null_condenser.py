"""NullCondenser — trivial CondenserPort adapter that returns messages unchanged.

The default condenser when no LLM-based compaction is configured;
also the test anchor for CondenserPort runtime-checkable conformance.

Relocated from src.reward_bench.use_cases.condenser_port in cycle 116.
"""
from typing import Tuple

from src.reward_bench.entities.condenser_config import CondenserConfig


class NullCondenser:
    """Returns messages unchanged. Default when no LLM compaction is wanted."""

    def condense(
        self,
        messages: Tuple[dict, ...],
        config: CondenserConfig,
    ) -> Tuple[dict, ...]:
        return tuple(messages)
