"""FakeInferenceOrchestrator — in-memory test adapter for InferenceOrchestrator Port.

Records every `ensure_serving` call onto `self.calls` for test
assertions. Returns a scripted `base_url`. Can be configured to raise
`TimeoutError` for specific `served_name`s to exercise failure paths
without touching Docker.
"""
from __future__ import annotations

from typing import Iterable

from src.ports.inference_orchestrator import InferenceOrchestrator
from src.reward_bench.entities.model_target import ModelTarget


class FakeInferenceOrchestrator(InferenceOrchestrator):
    """Test-only InferenceOrchestrator: scripted URL + call recording."""

    def __init__(
        self,
        base_url: str = "http://fake-vllm:8000",
        timeout_targets: Iterable[str] = (),
    ):
        self.base_url = base_url
        self.timeout_targets = frozenset(timeout_targets)
        self.calls: list[ModelTarget] = []

    def ensure_serving(self, target: ModelTarget) -> str:
        self.calls.append(target)
        if target.served_name in self.timeout_targets:
            raise TimeoutError(
                f"fake inference orchestrator: configured to timeout for "
                f"{target.served_name!r}"
            )
        return self.base_url
