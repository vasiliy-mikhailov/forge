"""InferenceOrchestrator — "ensure a model is being served, return its base URL"."""
from __future__ import annotations

from typing import Protocol

from src.reward_bench.entities.model_target import ModelTarget


class InferenceOrchestrator(Protocol):
    """Ensures a target model is being served; returns its base URL."""

    def ensure_serving(self, target: ModelTarget) -> str:
        """(Re)provision the inference backend to serve `target`.

        Returns the base URL (no trailing slash) once the backend
        advertises `target.served_name` at /v1/models.

        MAY raise `TimeoutError` if the backend doesn't become
        healthy within the adapter's configured timeout.
        """
        ...
