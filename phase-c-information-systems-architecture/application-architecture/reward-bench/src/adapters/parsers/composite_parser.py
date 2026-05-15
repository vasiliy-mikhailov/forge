"""Cycle 98 / ADR 0011: CompositeParser adapter.

Tries child parsers in order; the first non-empty result wins.
Adapter to support models that emit in either surface (text-fenced
or OpenAI-structured) without the agent loop knowing which.

Production default per cycle 96:
    CompositeParser([FencedTextParser(), StructuredOpenAIParser()])

This preserves the cycle-9/58 text-fenced contract (qwen / gemma /
llama) as the primary surface and falls back to structured only when
the text-fenced pass yields zero.
"""
from __future__ import annotations

from src.ports.protocol_parser import AssistantReply, ProtocolParser, ToolCall


class CompositeParser(ProtocolParser):
    def __init__(self, parsers: list[ProtocolParser]):
        self._parsers = tuple(parsers)

    def extract(self, reply: AssistantReply) -> list[ToolCall]:
        for parser in self._parsers:
            calls = parser.extract(reply)
            if calls:
                return calls
        return []
