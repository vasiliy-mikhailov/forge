"""§4 live end-to-end meta-test for bench_main."""
from __future__ import annotations

import pytest


@pytest.mark.live
def test_when_bench_main_called_with_real_chain_then_returns_submission_with_solver_body_and_non_negative_score(
        vllm_base_url, vllm_api_key, monkeypatch):
    """§4 live: bench_main → OrchestrateSubagentPerIter →
    OpenHandsSolutionGenerator (real OpenHands SDK + real vLLM) →
    DockerCanonicalScorer (real docker) → Submission with a body
    extracted from the agent's fenced python block.

    max_iters=1 — one full OpenHands run, one canonical score.

    Fitness:
      - body contains `class Solver`
      - body is non-trivial (real code, not a stub)
      - score is a non-negative float (a crashing solver legitimately
        scores 0; that's the canonical scorer working correctly).

    Note: submission.walltime_sec is aggregate_walltime_sec from the
    canonical scorer = sum of per-game runtimes. A crashing solver
    aggregates to ~0s; that's correct semantics, not a chain failure.
    Not asserted.
    """
    # Arrange
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.frameworks.bench_main import bench_main
    from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY
    from src.tier1.entities.submission import Submission

    # bench_main reads VLLM_API_KEY from env via ensure_serving_model
    monkeypatch.setenv('VLLM_API_KEY', vllm_api_key)

    target = next(t for t in MODEL_REGISTRY if t.id == 'qwen3.6-27b-awq')
    cfg = BenchConfig(max_iters=1, hard_wall_sec=60.0, smoke_early_stop=False)

    # Act
    submission = bench_main(target, cfg)

    # Assert
    assert isinstance(submission, Submission)
    assert 'class Solver' in submission.body, (
        f'submission.body missing Solver class; got first 400 chars: '
        f'{submission.body[:400]!r}'
    )
    assert len(submission.body) >= 200, (
        f'submission.body suspiciously short ({len(submission.body)} chars); '
        f'expected real code. Got: {submission.body!r}'
    )
    assert isinstance(submission.score, float) and submission.score >= 0, (
        f'submission.score expected non-negative float; got {submission.score!r}'
    )
