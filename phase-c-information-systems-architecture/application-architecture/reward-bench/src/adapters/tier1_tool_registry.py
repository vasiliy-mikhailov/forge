"""Tier1ToolRegistry adapter — composes the cycle-9/58 tier-1 tools.

Owns the tier-1 tool surface (view / execute_submission / finish)
plus the cycle-96 OpenAI tool schemas. After the cycle-114
rule-of-three lift, the per-tool dispatch logic lives in dedicated
`Tool` adapters under `src/adapters/tools/`; this registry composes
them via a `dict[str, Tool]` lookup.

Tier 2..4 will provide their own ToolRegistry adapters with
different tool surfaces, each composing its own set of Tool adapters.
"""
from __future__ import annotations

from src.adapters.tools.execute_submission_tool import ExecuteSubmissionTool
from src.adapters.tools.finish_tool import FinishTool
from src.adapters.tools.view_tool import ViewTool
from src.ports.tool import Tool
from src.ports.tool_registry import ToolContext, ToolRegistry


class Tier1ToolRegistry(ToolRegistry):
    """Composes the tier-1 tool surface: view / execute_submission / finish."""

    def __init__(self, tools: tuple[Tool, ...] | None = None):
        if tools is None:
            tools = (ViewTool(), ExecuteSubmissionTool(), FinishTool())
        self._tools: dict[str, Tool] = {t.name: t for t in tools}

    @property
    def schemas(self) -> tuple[dict, ...]:
        return tuple(t.schema for t in self._tools.values())

    def dispatch(self, name: str, args: dict, ctx: ToolContext) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return f'<error>unknown tool: {name}</error>'
        return tool.dispatch(args, ctx)
