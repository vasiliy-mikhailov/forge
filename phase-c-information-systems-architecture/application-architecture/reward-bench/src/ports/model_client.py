"""Cycle 98b / ADR 0011: ModelClient port.

A ModelClient sends messages to a model server and returns the
assistant's reply. Implementations encapsulate the wire protocol
(HTTP path, auth, payload shape) so the agent loop stays
implementation-free.
"""
from __future__ import annotations

from typing import Protocol

from src.ports.protocol_parser import AssistantReply


class ModelClient(Protocol):
    """Sends messages to a model and returns the assistant reply."""

    def call(
        self,
        messages: list[dict],
        *,
        tools: list[dict] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 12288,
        model_id: str | None = None,
    ) -> AssistantReply: ...
