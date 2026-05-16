"""CondenserPort — abstraction over SPEC.md context-compaction.

Adapters under src/reward_bench/adapters/ implement this interface.
The canonical adapter is LlmCondenser (compacts older turns into a
summary via the bench LLM). The trivial NullCondenser lives at
src/reward_bench/adapters/null_condenser.py and serves as the default
when no compaction is wanted.

Relocated from src.reward_bench.use_cases.condenser_port in cycle 116
to comply with ADR 0018's src/ports/<name>.py convention.
"""
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
