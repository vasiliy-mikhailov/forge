"""LlmCondenser: CondenserPort impl that replaces older turns with a summary.

See src-spec/reward_bench/adapters/llm_condenser/.

Per reward-bench/SOLUTION-ARCHITECTURE.md, the
wiring layer supplies a `summarise` callable backed by the bench-model vLLM
endpoint.

Two gates control when compaction fires (both must hold):

1. **Token gate** — `total_estimated_tokens > config.trigger_tokens`.
   Token count is estimated as `sum(len(content) // 4)` — a cheap
   4-chars-per-token heuristic. Without this gate the condenser
   over-fires on short turns and inflates wall time.
2. **Count gate** — `len(messages) > 1 + config.keep_recent`. Without
   this there is nothing structurally to compact.

When both gates pass, older turns (between the system message and
the `keep_recent` window) are summarised and the summary is APPENDED
to the existing system message's content (chat-template invariant —
qwen3.6 requires exactly one system message at position 0)."""
from typing import Callable, Tuple

from src.reward_bench.entities.condenser_config import CondenserConfig


def _estimate_tokens(messages: Tuple[dict, ...]) -> int:
    """4-chars-per-token heuristic across message contents."""
    return sum(len(m.get('content', '')) // 4 for m in messages)


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
        # Both gates must pass.
        if n <= 1 + config.keep_recent:
            return tuple(messages)
        if _estimate_tokens(messages) <= config.trigger_tokens:
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
