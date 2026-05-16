"""Tool — the runtime-boundary Port for a single tool the agent may invoke.

The agent's `ToolRegistry` (cycle 98c) catalogues a set of Tools and
dispatches by name. Each Tool implements this protocol: it advertises
an OpenAI tool schema and accepts `(args, ctx) -> observation_str`.

Lifted in cycle 114 from the switch-by-name dispatch inside
`Tier1ToolRegistry` per the cycle-113 "rule of three" CATS rule
(three implementations — view, execute_submission, finish — sharing
the same dispatch shape).
"""
from __future__ import annotations

from typing import Protocol

from src.ports.tool_registry import ToolContext


class Tool(Protocol):
    """A single tool the agent can call.

    Implementations advertise an OpenAI tool schema and run on demand.
    """

    @property
    def name(self) -> str:
        """The name the model uses to invoke this tool.

        Matches `schema['function']['name']`.
        """
        ...

    @property
    def schema(self) -> dict:
        """The OpenAI tool-call schema advertised in `tools=[...]`.

        Same shape as a single entry in `ToolRegistry.schemas`.
        """
        ...

    def dispatch(self, args: dict, ctx: ToolContext) -> str:
        """Run the tool and return the observation string.

        MUST NOT raise on malformed `args` — return an `<error>` string
        instead (mirrors `ToolRegistry.dispatch`'s contract).
        """
        ...
