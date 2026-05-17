"""CondenserPort — abstraction over context-compaction."""
from typing import Protocol, Tuple, runtime_checkable

from src.reward_bench.entities.condenser_config import CondenserConfig


@runtime_checkable
class CondenserPort(Protocol):
    """Summarises older turns when prompt + reserved output exceeds the budget."""

    def condense(
        self,
        messages: Tuple[dict, ...],
        config: CondenserConfig,
    ) -> Tuple[dict, ...]:
        """Return condensed messages; recent `config.keep_recent` turns must pass through."""
        ...
