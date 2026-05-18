"""OrchestrateRalphSingleContext adapter tests."""
from __future__ import annotations


def test_when_orchestrate_ralph_single_context_called_then_yielded_submission_score_equals_run_loop_best_dev_mean():
    """Pins the §7 ralph-adapter score mapping:
    run_loop's `best_dev_mean` → `Submission.score`."""
    # Arrange
    from pathlib import Path

    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        OrchestrateRalphSingleContext,
    )
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env

    def fake_run_loop(**_):
        return {
            'iterations': 5,
            'messages': [],
            'finished': True,
            'best_dev_mean': 42.5,
        }

    adapter = OrchestrateRalphSingleContext(run_loop_fn=fake_run_loop)
    env = Env(tasks_dir=Path('/tmp/x'), canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig()

    # Act
    submissions = list(adapter.orchestrate(env, cfg))

    # Assert
    assert submissions[0].score == 42.5
