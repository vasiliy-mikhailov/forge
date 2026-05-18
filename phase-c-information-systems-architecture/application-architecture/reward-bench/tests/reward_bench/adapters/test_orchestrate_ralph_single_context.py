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
            'body': '',
            'walltime_sec': 0.0,
        }

    adapter = OrchestrateRalphSingleContext(run_loop_fn=fake_run_loop)
    env = Env(tasks_dir=Path('/tmp/x'), canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig()

    # Act
    submissions = list(adapter.orchestrate(env, cfg))

    # Assert
    assert submissions[0].score == 42.5


def test_when_orchestrate_ralph_single_context_called_then_yielded_submission_body_equals_run_loop_result_body():
    """Pins the §7 ralph-adapter body mapping:
    run_loop_fn result['body'] → Submission.body."""
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
            'body': 'class Solver: pass\n',
            'walltime_sec': 0.0,
        }

    adapter = OrchestrateRalphSingleContext(run_loop_fn=fake_run_loop)
    env = Env(tasks_dir=Path('/tmp/x'), canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig()

    # Act
    submissions = list(adapter.orchestrate(env, cfg))

    # Assert
    assert submissions[0].body == 'class Solver: pass\n'


def test_when_orchestrate_ralph_single_context_called_then_yielded_submission_walltime_sec_equals_run_loop_result_walltime_sec():
    """Pins the §7 ralph-adapter walltime mapping:
    run_loop_fn result['walltime_sec'] → Submission.walltime_sec."""
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
            'body': '',
            'walltime_sec': 137.25,
        }

    adapter = OrchestrateRalphSingleContext(run_loop_fn=fake_run_loop)
    env = Env(tasks_dir=Path('/tmp/x'), canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig()

    # Act
    submissions = list(adapter.orchestrate(env, cfg))

    # Assert
    assert submissions[0].walltime_sec == 137.25


def test_when_run_loop_with_metrics_called_then_result_walltime_sec_equals_time_delta():
    """Pins the §7 ralph production wrapper's walltime measurement:
    result['walltime_sec'] equals the monotonic delta around the inner
    run_loop call."""
    # Arrange
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        run_loop_with_metrics,
    )

    times = iter([100.0, 137.25])

    def fake_time_fn():
        return next(times)

    def fake_run_loop(**_):
        return {
            'iterations': 0,
            'messages': [],
            'finished': False,
            'best_dev_mean': 0.0,
        }

    # Act
    result = run_loop_with_metrics(
        _run_loop=fake_run_loop,
        _time_fn=fake_time_fn,
    )

    # Assert
    assert result['walltime_sec'] == 37.25
