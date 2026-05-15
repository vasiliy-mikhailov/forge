"""Cycle 99a / ADR 0012: FakeModelClient adapter.

Returns scripted AssistantReply values in order; ignores messages /
tools / model_id (logs them on `.calls` so tests can inspect what
the loop sent). Used to exercise the entire agent loop end-to-end
without a vLLM container.
"""
from __future__ import annotations

from src.ports.model_client import ModelClient
from src.ports.protocol_parser import AssistantReply


class FakeModelClient(ModelClient):
    """In-memory scripted ModelClient.

    Args:
        script: tuple of AssistantReply dicts. Returned in order on
            each call. If the script is exhausted, the last reply is
            repeated (so a runaway loop stalls cleanly instead of
            crashing).
        repeat_last: when True (default), repeat the last script entry
            after exhaustion. When False, raise IndexError so tests
            can pin the exact iter count.
    """

    def __init__(
        self,
        script: tuple[AssistantReply, ...] | list[AssistantReply],
        *,
        repeat_last: bool = True,
    ):
        self._script = tuple(script)
        self._repeat_last = repeat_last
        self._i = 0
        self.calls: list[dict] = []   # observability for assertions

    def call(
        self,
        messages: list[dict],
        *,
        tools: list[dict] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 12288,
        model_id: str | None = None,
    ) -> AssistantReply:
        self.calls.append({
            'messages': messages,
            'tools': tools,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'model_id': model_id,
        })
        if self._i < len(self._script):
            reply = self._script[self._i]
            self._i += 1
        elif self._repeat_last and self._script:
            reply = self._script[-1]
        else:
            raise IndexError(
                f'FakeModelClient script exhausted after {self._i} calls'
            )
        # Defensive normalisation to match the AssistantReply contract.
        return {
            'content': reply.get('content', '') or '',
            'tool_calls': reply.get('tool_calls') or [],
        }
