"""InferenceOrchestrator — Port for "ensure a model is being served, return its base URL."

The production binding spawns/reconciles a Docker vLLM container per
ADR 0001 + ADR 0006. The Fake returns scripted URLs in-memory and
records calls for test assertions.

Per ADR 0018 (amended cycle 113), a free function that crosses a
runtime boundary (subprocess + HTTP here) becomes a Port. This Port
codifies what was historically the `ensure_serving_model` free
function in src/tier1/inference.py.
"""
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
        healthy within the adapter's configured timeout — that's
        infrastructure failure, not a bench bug we can recover from
        in-loop.
        """
        ...
