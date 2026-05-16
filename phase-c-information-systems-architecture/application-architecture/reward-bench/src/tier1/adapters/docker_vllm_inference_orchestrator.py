"""DockerVllmInferenceOrchestrator — InferenceOrchestrator binding for Docker + vLLM.

Production class wrapping the existing `ensure_serving_model` free
function in src/tier1/inference.py. Created in cycle 117 as part of
the ADR 0018 backsweep — the free function predates the Port
discipline and is now Port-conformant via this thin class.

Why a thin wrapper instead of moving the logic? Per the cycle-113
minimal-implementation discipline: the lift is structural (so the
Port exists and the architecture test enforces it). Moving the
container-management logic into the class is a separate refactor
that can happen incrementally without risking regression in the
already-tested free function.
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
