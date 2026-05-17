"""CompositeParser adapter.

Tries child parsers in order; the first non-empty result wins.
Production default: CompositeParser([FencedTextParser(),
StructuredOpenAIParser()]) — text-fenced primary, structured fallback.
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
