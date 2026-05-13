"""CondenserPort: application-layer abstraction over the SPEC.md
context-compaction step.

See src-spec/reward_bench/use_cases/condenser_port/."""
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


class NullCondenser:
    """Trivial implementation: returns messages unchanged.

    Useful as the default when the conversation is below the trigger
    budget and as a test anchor for the protocol."""

    def condense(
        self,
        messages: Tuple[dict, ...],
        config: CondenserConfig,
    ) -> Tuple[dict, ...]:
        return tuple(messages)
