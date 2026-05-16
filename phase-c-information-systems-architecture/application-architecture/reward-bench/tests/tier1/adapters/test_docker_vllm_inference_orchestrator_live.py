"""Cycle 124: DockerVllmInferenceOrchestrator live-runtime test per cycle 122.

Invokes the orchestrator against the real Docker + vLLM stack. Uses
the lab's canary model (qwen3.6-27b-awq) so the test exercises the
idempotent path when the container is already serving it (fast) and
the full provision path otherwise (slow ~5 min).

@pytest.mark.live — opt-in via `pytest -m live`. Setup may swap the
vLLM container (expected; per user clarification, live tests are
allowed to wipe out a concurrent production-runtime bench).
"""
from __future__ import annotations

import urllib.request

import pytest

from src.reward_bench.entities.model_target import ModelTarget
from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY
from src.tier1.adapters.docker_vllm_inference_orchestrator import (
    DockerVllmInferenceOrchestrator,
)


def _canary_target() -> ModelTarget:
    """The lab canary model — small enough to warm up reasonably."""
    by_id = {t.id: t for t in MODEL_REGISTRY}
    return by_id["qwen3.6-27b-awq"]


@pytest.mark.live
def test_when_orchestrator_ensure_serving_called_with_canary_then_returns_reachable_base_url(
    vllm_api_key,
):
    # Arrange
    orchestrator = DockerVllmInferenceOrchestrator()
    target = _canary_target()

    # Act — may take seconds (idempotent) or minutes (cold restart).
    base_url = orchestrator.ensure_serving(target)

    # Assert: shape of returned URL
    assert isinstance(base_url, str)
    assert base_url.startswith("http://")
    assert ":8000" in base_url

    # Assert: /v1/models advertises target.served_name
    req = urllib.request.Request(
        f"{base_url}/v1/models",
        headers={"Authorization": f"Bearer {vllm_api_key}"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        assert r.status == 200
        body = r.read().decode("utf-8", errors="replace")
    assert target.served_name in body, (
        f"served_name {target.served_name!r} not advertised at "
        f"{base_url}/v1/models; body={body[:300]}"
    )


@pytest.mark.live
def test_when_orchestrator_called_twice_with_same_target_then_idempotent(
    vllm_api_key,
):
    """Calling ensure_serving twice with the same target must NOT
    restart the container — the second call returns the same URL
    without side effects."""
    # Arrange
    orchestrator = DockerVllmInferenceOrchestrator()
    target = _canary_target()

    # Act — first call may restart; second must be a no-op.
    url1 = orchestrator.ensure_serving(target)
    url2 = orchestrator.ensure_serving(target)

    # Assert
    assert url1 == url2, (
        f"idempotent-call URLs differ: {url1!r} vs {url2!r}"
    )
