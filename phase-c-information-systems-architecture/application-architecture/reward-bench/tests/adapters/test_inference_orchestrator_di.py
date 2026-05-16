"""Cycle 117: contract tests for InferenceOrchestrator Port + adapters."""
from __future__ import annotations

import pytest

from src.adapters.fakes.fake_inference_orchestrator import FakeInferenceOrchestrator
from src.ports.inference_orchestrator import InferenceOrchestrator
from src.reward_bench.entities.model_target import ModelTarget
from src.tier1.adapters.docker_vllm_inference_orchestrator import (
    DockerVllmInferenceOrchestrator,
)


_TARGET = ModelTarget(
    id="fake-test-model",
    hf_path="fake/fake-test-model",
    served_name="fake-test-model",
    max_model_len=4096,
    tool_call_parser="qwen3_xml",
)


@pytest.mark.no_fake
def test_when_inference_orchestrator_port_inspected_then_has_ensure_serving_method():
    # Arrange + Act
    has_method = hasattr(InferenceOrchestrator, "ensure_serving")

    # Assert
    assert has_method


@pytest.mark.no_fake
def test_when_docker_vllm_inference_orchestrator_inspected_then_implements_port():
    # Arrange + Act
    instance = DockerVllmInferenceOrchestrator()

    # Assert: declares Port inheritance (Protocol — duck-typed; check method).
    assert callable(getattr(instance, "ensure_serving", None))


@pytest.mark.no_fake
def test_when_fake_orchestrator_called_then_records_target_and_returns_scripted_url():
    # Arrange
    fake = FakeInferenceOrchestrator(base_url="http://example:8000")

    # Act
    url = fake.ensure_serving(_TARGET)

    # Assert
    assert url == "http://example:8000"
    assert fake.calls == [_TARGET]


@pytest.mark.no_fake
def test_when_fake_orchestrator_configured_timeout_then_raises_timeout_error():
    # Arrange
    fake = FakeInferenceOrchestrator(
        timeout_targets=("fake-test-model",),
    )

    # Act + Assert
    with pytest.raises(TimeoutError):
        fake.ensure_serving(_TARGET)
