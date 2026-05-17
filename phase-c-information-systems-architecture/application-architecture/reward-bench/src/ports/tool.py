"""Tool — the runtime-boundary Port for a single tool the agent may invoke."""
from __future__ import annotations

from typing import Protocol

from src.ports.tool_registry import ToolContext


class Tool(Protocol):
    """A single tool the agent can call.

    Implementations advertise an OpenAI tool schema and run on demand.
    """

    @property
    def name(self) -> str:
        """The name the model uses to invoke this tool."""
        ...

    @property
    def schema(self) -> dict:
        """The OpenAI tool-call schema advertised in `tools=[...]`."""
        ...

    def dispatch(self, args: dict, ctx: ToolContext) -> str:
        """Run the tool and return the observation string.

        MUST NOT raise on malformed `args` — return an `<error>` string instead.
        """
        ...
