"""ViewTool — reads a file from /workspace, /env, or /tasks; defends ../ escape.

`Tool` Port adapter. Behaviour lifted verbatim from
`Tier1ToolRegistry.dispatch` (cycle 114).
"""
from __future__ import annotations

from pathlib import Path

from src.ports.tool import Tool
from src.ports.tool_registry import ToolContext


_VIEW_SCHEMA = {
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
}


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


class ViewTool(Tool):
    """Reads files from /workspace, /env, or /tasks with path-escape protection."""

    @property
    def name(self) -> str:
        return "view"

    @property
    def schema(self) -> dict:
        return _VIEW_SCHEMA

    def dispatch(self, args: dict, ctx: ToolContext) -> str:
        workspace = ctx['workspace']
        env_dir = ctx['env_dir']
        tasks_dir = ctx['tasks_dir']
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
