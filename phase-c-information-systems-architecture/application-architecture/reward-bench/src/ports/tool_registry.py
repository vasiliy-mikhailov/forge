"""Cycle 98c / ADR 0011: ToolRegistry port.

A ToolRegistry knows two things:
  - `schemas` — the OpenAI tool advertisement (cycle 96).
  - `dispatch(name, args, ctx)` — given a tool call, produce an
    observation string for the next prompt turn.

The agent loop is a registry user; tier 2..4 will provide their own
registries (langgraph, openhands, orchestrator). The cycle-9/58
tool surface (view / execute_submission / finish) lives in
`Tier1ToolRegistry`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, TypedDict


class ToolContext(TypedDict, total=False):
    """Per-iter context the registry needs for some tools.

    Optional because not all tools care about every field; the
    registry asks for what it needs.
    """
    workspace: Path
    env_dir: Path
    tasks_dir: Path
    dev_hard_wall_sec: float | None   # cycle 77 / ADR 0006


class ToolRegistry(Protocol):
    """Catalog + dispatcher for the agent's tool surface."""

    @property
    def schemas(self) -> tuple[dict, ...]:
        """OpenAI tool-call schemas advertised in `tools=[...]`."""
        ...

    def dispatch(self, name: str, args: dict, ctx: ToolContext) -> str:
        """Return the observation string for the next prompt turn."""
        ...
