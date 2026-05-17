"""DockerVllmInferenceOrchestrator — InferenceOrchestrator binding for Docker + vLLM.

Thin wrapper around `src.tier1.inference.ensure_serving_model`.
"""
from __future__ import annotations

from src.ports.inference_orchestrator import InferenceOrchestrator
from src.reward_bench.entities.model_target import ModelTarget


class DockerVllmInferenceOrchestrator(InferenceOrchestrator):
    """Docker + vLLM inference orchestrator.

    Delegates to `src.tier1.inference.ensure_serving_model`, which
    spawns/reconciles the `reward-bench-vllm` Docker container.
    """

    def ensure_serving(self, target: ModelTarget) -> str:
        # Lazy import: keeps the class constructable in tests that
        # don't exercise Docker (the autouse fake-binding pattern
        # never reaches this body).
        from src.tier1.inference import ensure_serving_model
        return ensure_serving_model(target)
