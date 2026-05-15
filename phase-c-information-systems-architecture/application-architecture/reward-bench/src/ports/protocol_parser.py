"""Cycle 98 / ADR 0011: ProtocolParser port + AssistantReply type.

A ProtocolParser extracts (name, args) tool calls from an
AssistantReply. Different adapters handle different surfaces:
  - FencedTextParser  — cycle 9/58 ```tool fenced blocks
  - StructuredOpenAIParser — cycle 83/96 message.tool_calls
  - CompositeParser   — tries children in order, first non-empty wins

The port keeps the agent loop free of polyglot knowledge: it just
asks the configured parser for tool calls.
"""
from __future__ import annotations

from typing import NamedTuple, Protocol, TypedDict


class AssistantReply(TypedDict):
    """The shape `ModelClient` returns. Both surfaces possible."""
    content: str
    tool_calls: list[dict]   # OpenAI tool_calls shape; may be empty


class ToolCall(NamedTuple):
    """A parsed tool invocation ready for `ToolRegistry.dispatch`."""
    name: str
    args: dict


class ProtocolParser(Protocol):
    """Extracts ToolCalls from an AssistantReply.

    Implementations MUST NOT raise on malformed input (per cycle 51
    defensive-parser contract); they return [] and let the agent loop
    treat it as a no-tool-call iter.
    """
    def extract(self, reply: AssistantReply) -> list[ToolCall]: ...
