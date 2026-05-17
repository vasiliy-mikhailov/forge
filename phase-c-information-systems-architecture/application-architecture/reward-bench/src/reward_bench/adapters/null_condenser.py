"""NullCondenser — trivial CondenserPort adapter that returns messages unchanged."""
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
