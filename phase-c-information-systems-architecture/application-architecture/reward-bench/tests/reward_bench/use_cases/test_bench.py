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
