"""LlmCondenser: CondenserPort impl that replaces older turns with a summary.

See src-spec/reward_bench/adapters/llm_condenser/.

Per reward-bench/docs/adr/0001-condenser-uses-same-model-as-bench.md, the
wiring layer supplies a `summarise` callable backed by the bench-model vLLM
endpoint. This adapter keeps the compaction logic separate from the LLM
call so it is testable without a live model."""
from typing import Callable, Tuple

from src.reward_bench.entities.condenser_config import CondenserConfig


class LlmCondenser:
    """Replaces older turns with one summary message produced by `summarise`."""

    def __init__(
        self,
        summarise: Callable[[Tuple[dict, ...]], str],
        model_id: str,
    ):
        self._summarise = summarise
        self.model_id = model_id

    def condense(
        self,
        messages: Tuple[dict, ...],
        config: CondenserConfig,
    ) -> Tuple[dict, ...]:
        n = len(messages)
        if n <= 1 + config.keep_recent:
            return tuple(messages)
        system = messages[0]
        recent = tuple(messages[-config.keep_recent:])
        older = tuple(messages[1:-config.keep_recent])
        summary = self._summarise(older)
        summary_msg = {
            'role': 'system',
            'content': f'[summary of {len(older)} earlier turns] {summary}',
        }
        return (system, summary_msg) + recent
