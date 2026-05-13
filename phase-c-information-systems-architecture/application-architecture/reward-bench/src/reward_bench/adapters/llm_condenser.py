"""LlmCondenser: CondenserPort impl that replaces older turns with a summary.

See src-spec/reward_bench/adapters/llm_condenser/.

Per reward-bench/docs/adr/0001-condenser-uses-same-model-as-bench.md, the
wiring layer supplies a `summarise` callable backed by the bench-model vLLM
endpoint.

Chat-template invariant: most chat templates (including qwen3.6) require
the system message to be the FIRST message AND require AT MOST ONE system
message. So the summary is APPENDED to the existing system message's
content — never inserted as a second system message. This is the cycle-20
correction of cycle 18's contract that surfaced when the bench actually
ran end-to-end against vLLM."""
from typing import Callable, Tuple

from src.reward_bench.entities.condenser_config import CondenserConfig


class LlmCondenser:
    """Compacts older turns into a summary appended to the system message."""

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
        merged_system = {
            'role': 'system',
            'content': (
                system['content']
                + f'\n\n[Summary of {len(older)} earlier turns]\n{summary}'
            ),
        }
        return (merged_system,) + recent
