"""FinishTool — signals end of loop; emits `<finish>{note}</finish>`."""
from __future__ import annotations

from src.ports.tool import Tool
from src.ports.tool_registry import ToolContext


_FINISH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "finish",
        "description": (
            "End the loop. The body of the most recent successful "
            "execute_submission is promoted to /workspace/submission.py "
            "for canonical scoring."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "note": {
                    "type": "string",
                    "description": "Optional reasoning for stopping.",
                },
            },
        },
    },
}


class FinishTool(Tool):
    """Signals end of loop; returns `<finish>{note}</finish>`."""

    @property
    def name(self) -> str:
        return "finish"

    @property
    def schema(self) -> dict:
        return _FINISH_SCHEMA

    def dispatch(self, args: dict, ctx: ToolContext) -> str:
        note = args.get('note', '')
        return f'<finish>{note}</finish>'
