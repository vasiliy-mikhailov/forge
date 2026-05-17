"""ProtocolParser port + AssistantReply type."""
from __future__ import annotations

from typing import NamedTuple, Protocol, TypedDict


class AssistantReply(TypedDict):
    """The shape `ModelClient` returns. Both surfaces possible."""
    content: str
    tool_calls: list[dict]


class ToolCall(NamedTuple):
    """A parsed tool invocation ready for `ToolRegistry.dispatch`."""
    name: str
    args: dict


class ProtocolParser(Protocol):
    """Extracts ToolCalls from an AssistantReply.

    Implementations MUST NOT raise on malformed input; they return []
    and let the agent loop treat it as a no-tool-call iter.
    """
    def extract(self, reply: AssistantReply) -> list[ToolCall]: ...
