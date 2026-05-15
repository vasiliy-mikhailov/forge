"""Cycle 98c / ADR 0011: Tier1ToolRegistry adapter.

Owns the cycle-9/58 tool surface (view / execute_submission / finish)
plus the cycle-96 OpenAI tool schemas. Lifted verbatim from
pre-cycle-98c `execute_tool` + `TOOL_SCHEMAS` in
src/tier1/agent_loop.py.

Tier 2..4 will provide their own ToolRegistry adapters with different
tool surfaces.
"""
from __future__ import annotations

from pathlib import Path

from src.ports.tool_registry import ToolContext, ToolRegistry


# Cycle 96 schema catalog — mirrors SYSTEM_PROMPT.
_TOOL_SCHEMAS: tuple[dict, ...] = (
    {
        "type": "function",
        "function": {
            "name": "view",
            "description": (
                "Read a file from /workspace, /env, or /tasks into the "
                "next assistant prompt. Use /tasks/2048/SKILL_tier1.md "
                "first to learn the contract."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Absolute path beginning with /workspace, "
                            "/env, or /tasks."
                        ),
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
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
    },
    {
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
    },
)


def _trim(s: str, n: int = 4000) -> str:
    if len(s) <= n:
        return s
    return s[: n - 200] + f"\n... [truncated, total {len(s)} chars]"


def _virt_to_host(virt: str, workspace: Path, env_dir: Path,
                  tasks_dir: Path) -> Path | None:
    """Resolve a model-supplied virtual path to a host path. Returns
    None if the path doesn't sit under one of the allowed virtual roots."""
    if not virt:
        return None
    p = virt.strip()
    while '//' in p:
        p = p.replace('//', '/')
    for prefix, root in (('/workspace', workspace),
                         ('/env', env_dir),
                         ('/tasks', tasks_dir)):
        if p == prefix or p.startswith(prefix + '/'):
            tail = p[len(prefix):].lstrip('/')
            host = (Path(root) / tail).resolve() if tail else Path(root).resolve()
            # Defence-in-depth: post-resolve check to block ../ escapes.
            if not str(host).startswith(str(Path(root).resolve())):
                return None
            return host
    return None


class Tier1ToolRegistry(ToolRegistry):
    """Cycle-9/58 tier-1 tool surface — view / execute_submission / finish."""

    @property
    def schemas(self) -> tuple[dict, ...]:
        return _TOOL_SCHEMAS

    def dispatch(self, name: str, args: dict, ctx: ToolContext) -> str:
        workspace = ctx['workspace']
        env_dir = ctx['env_dir']
        tasks_dir = ctx['tasks_dir']
        dev_hard_wall_sec = ctx.get('dev_hard_wall_sec')

        if name == 'view':
            virt = args.get('path', '')
            host = _virt_to_host(virt, workspace, env_dir, tasks_dir)
            if host is None:
                return (f'<error>view: path must start with /workspace, '
                        f'/env, or /tasks (got {virt!r})</error>')
            if not host.exists():
                return f'<error>view: file not found: {virt}</error>'
            try:
                return f'<view path="{virt}">\n{_trim(host.read_text())}\n</view>'
            except Exception as e:
                return f'<error>view: {e}</error>'

        if name == 'finish':
            note = args.get('note', '')
            return f'<finish>{note}</finish>'

        if name == 'execute_submission':
            # Cycle 58 / ADR 0008: ralph-loop atomic primitive.
            body = args.get('content', '')
            # Lazy import to keep the registry constructable in tests
            # that don't exercise the actual dev runner.
            from src.tier1.agent_loop import _execute_submission
            return _execute_submission(body, workspace, tasks_dir,
                                       dev_hard_wall_sec=dev_hard_wall_sec)

        return f'<error>unknown tool: {name}</error>'
