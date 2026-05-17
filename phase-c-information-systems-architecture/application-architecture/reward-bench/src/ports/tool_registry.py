"""ToolRegistry port."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, TypedDict


class ToolContext(TypedDict, total=False):
    """Per-iter context the registry needs for some tools."""
    workspace: Path
    env_dir: Path
    tasks_dir: Path
    dev_hard_wall_sec: float | None


class ToolRegistry(Protocol):
    """Catalog + dispatcher for the agent's tool surface."""

    @property
    def schemas(self) -> tuple[dict, ...]:
        """OpenAI tool-call schemas advertised in `tools=[...]`."""
        ...

    def dispatch(self, name: str, args: dict, ctx: ToolContext) -> str:
        """Return the observation string for the next prompt turn."""
        ...
