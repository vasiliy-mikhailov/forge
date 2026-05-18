"""bench top-level composition tests."""
from __future__ import annotations


def test_when_bench_run_with_orchestrator_then_returns_best_scored_submission():
    """Pins the §7 composition `bench = argmaxBy (.score) (orchestrate)`.
    A fake Orchestrator yields two Submissions; bench returns the higher
    scored one."""
    # Arrange
    from pathlib import Path

    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env
    from src.reward_bench.use_cases.bench import bench
    from src.tier1.entities.submission import Submission

    a = Submission(body='from foo import bar\n', score=10.0, walltime_sec=1.0)
    b = Submission(body='from baz import qux\n', score=20.0, walltime_sec=2.0)

    class FakeOrch:
        def orchestrate(self, env, cfg):
            return [a, b]

    env = Env(tasks_dir=Path('/tmp/x'), canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig()

    # Act
    result = bench(FakeOrch(), env, cfg)

    # Assert
    assert result is b


import pytest


@pytest.mark.live
def test_when_bench_called_with_real_ralph_chain_then_returns_submission(
        vllm_base_url, vllm_api_key):
    """§7 end-to-end live: bench → adapter → wrapper → real run_loop
    against real vLLM + real Docker scorer returns a Submission."""
    # Arrange
    from pathlib import Path

    from src.adapters.vllm_openai_client import VllmOpenAIClient
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        OrchestrateRalphSingleContext,
        default_run_loop_fn,
    )
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env
    from src.reward_bench.use_cases.bench import bench
    from src.tier1.adapters.docker_canonical_scorer import (
        DockerCanonicalScorer,
    )
    from src.tier1.entities.submission import Submission

    repo_root = Path(__file__).resolve().parents[3]
    tasks_dir = repo_root / 'tasks'

    env = Env(
        tasks_dir=tasks_dir,
        canonical_scorer=DockerCanonicalScorer(),
        model_client=VllmOpenAIClient(
            base_url=vllm_base_url,
            api_key=vllm_api_key,
            default_model_id='qwen3.6-27b-awq',
        ),
    )
    cfg = BenchConfig(max_iters=2, hard_wall_sec=60.0)
    adapter = OrchestrateRalphSingleContext(
        run_loop_fn=default_run_loop_fn(),
    )

    # Act
    submission = bench(adapter, env, cfg)

    # Assert
    assert isinstance(submission, Submission)
