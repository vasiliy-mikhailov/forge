"""ExecuteSubmissionTool — runs a submission body in the dev sandbox.

`Tool` Port adapter. Behaviour lifted verbatim from
`Tier1ToolRegistry.dispatch` (cycle 114). The Docker invocation lives
in `_execute_submission` (ADR 0008); this adapter wraps it as a Tool.
"""
from __future__ import annotations

from src.ports.tool import Tool
from src.ports.tool_registry import ToolContext


_EXECUTE_SUBMISSION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_submission",
        "description": (
            "Write a submission body into a sandboxed tier-1 dev runner "
            "and return per-seed scores. The body MUST be a Python "
            "module with `class Solver` exposing `move(board) -> "
            "'W'|'A'|'S'|'D'` and MUST import from transitions. "
            "Returns a JSON observation with protocol_violations, "
            "per_seed, mean, max_tile_best, walltime_sec_total."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": (
                        "Full Python submission body. Will be written "
                        "to /workspace/submission.py and executed."
                    ),
                },
            },
            "required": ["content"],
        },
    },
}


class ExecuteSubmissionTool(Tool):
    """Runs a submission body in the dev sandbox; returns JSON observation string."""

    @property
    def name(self) -> str:
        return "execute_submission"

    @property
    def schema(self) -> dict:
        return _EXECUTE_SUBMISSION_SCHEMA

    def dispatch(self, args: dict, ctx: ToolContext) -> str:
        # Lazy import keeps this adapter constructable in tests that
        # don't exercise the dev runner (and avoids agent_loop -> tools
        # -> agent_loop cycles).
        from src.tier1.agent_loop import _execute_submission
        workspace = ctx['workspace']
        tasks_dir = ctx['tasks_dir']
        dev_hard_wall_sec = ctx.get('dev_hard_wall_sec')
        body = args.get('content', '')
        return _execute_submission(body, workspace, tasks_dir,
                                   dev_hard_wall_sec=dev_hard_wall_sec)
