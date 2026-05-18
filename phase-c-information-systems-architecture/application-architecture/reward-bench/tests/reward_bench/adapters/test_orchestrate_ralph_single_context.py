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


def test_when_run_loop_with_metrics_given_body_reader_then_result_body_equals_reader_output():
    """Pins the §7 ralph wrapper's body-lifting seam: result['body']
    comes from an injected _body_reader, not from run_loop."""
    # Arrange
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        run_loop_with_metrics,
    )

    def fake_body_reader(workspace):
        return 'class Solver: pass\n'

    def fake_time_fn():
        return 0.0

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
        _body_reader=fake_body_reader,
        workspace='/tmp/ws',
    )

    # Assert
    assert result['body'] == 'class Solver: pass\n'


def test_when_default_run_loop_fn_called_then_body_is_read_from_workspace_submission_best_py(tmp_path):
    """Pins the §7 ralph production binding: the default factory's
    _body_reader reads workspace/submission.best.py from disk."""
    # Arrange
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        default_run_loop_fn,
    )

    body_text = 'class Solver: pass\n'
    (tmp_path / 'submission.best.py').write_text(body_text)

    def fake_inner(**_):
        return {
            'iterations': 0,
            'messages': [],
            'finished': False,
            'best_dev_mean': 0.0,
        }

    fn = default_run_loop_fn(_run_loop=fake_inner, _time_fn=lambda: 0.0)

    # Act
    result = fn(workspace=str(tmp_path))

    # Assert
    assert result['body'] == body_text


def test_when_default_run_loop_fn_called_with_empty_workspace_then_body_is_empty_string(tmp_path):
    """Pins §7 ralph production binding: when submission.best.py is
    absent (ralph finished without writing a best snapshot), the
    default _body_reader returns '' rather than raising."""
    # Arrange
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        default_run_loop_fn,
    )

    # tmp_path is intentionally empty — no submission.best.py

    def fake_inner(**_):
        return {
            'iterations': 0,
            'messages': [],
            'finished': False,
            'best_dev_mean': 0.0,
        }

    fn = default_run_loop_fn(_run_loop=fake_inner, _time_fn=lambda: 0.0)

    # Act
    result = fn(workspace=str(tmp_path))

    # Assert
    assert result['body'] == ''


def test_when_orchestrate_called_then_run_loop_fn_receives_tasks_dir_from_env(tmp_path):
    """Pins §7 ralph adapter kwarg pass-through: env.tasks_dir reaches
    the inner run_loop_fn as a tasks_dir kwarg."""
    # Arrange
    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        OrchestrateRalphSingleContext,
    )
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env

    captured: dict = {}

    def fake_run_loop(**kwargs):
        captured.update(kwargs)
        return {
            'iterations': 0,
            'messages': [],
            'finished': False,
            'best_dev_mean': 0.0,
            'body': '',
            'walltime_sec': 0.0,
        }

    adapter = OrchestrateRalphSingleContext(run_loop_fn=fake_run_loop)
    env = Env(tasks_dir=tmp_path, canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig()

    # Act
    list(adapter.orchestrate(env, cfg))

    # Assert
    assert captured['tasks_dir'] == tmp_path


def test_when_orchestrate_called_then_run_loop_fn_receives_max_iters_from_cfg(tmp_path):
    """Pins §7 ralph adapter cfg pass-through: cfg.max_iters reaches
    the inner run_loop_fn as a max_iters kwarg."""
    # Arrange
    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        OrchestrateRalphSingleContext,
    )
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env

    captured: dict = {}

    def fake_run_loop(**kwargs):
        captured.update(kwargs)
        return {
            'iterations': 0,
            'messages': [],
            'finished': False,
            'best_dev_mean': 0.0,
            'body': '',
            'walltime_sec': 0.0,
        }

    adapter = OrchestrateRalphSingleContext(run_loop_fn=fake_run_loop)
    env = Env(tasks_dir=tmp_path, canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig(max_iters=42)

    # Act
    list(adapter.orchestrate(env, cfg))

    # Assert
    assert captured['max_iters'] == 42


def test_when_orchestrate_called_then_run_loop_fn_receives_cfg_passthrough_kwargs(tmp_path):
    """Pins §7 ralph adapter cfg pass-through batch: temperature,
    finish_floor, supervisor_every_k, smoke_early_stop all flow
    unchanged from BenchConfig to run_loop_fn kwargs."""
    # Arrange
    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        OrchestrateRalphSingleContext,
    )
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env

    captured: dict = {}

    def fake_run_loop(**kwargs):
        captured.update(kwargs)
        return {
            'iterations': 0,
            'messages': [],
            'finished': False,
            'best_dev_mean': 0.0,
            'body': '',
            'walltime_sec': 0.0,
        }

    adapter = OrchestrateRalphSingleContext(run_loop_fn=fake_run_loop)
    env = Env(tasks_dir=tmp_path, canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig(
        temperature=0.5,
        finish_floor=0.3,
        supervisor_every_k=7,
        smoke_early_stop=True,
    )

    # Act
    list(adapter.orchestrate(env, cfg))

    # Assert
    assert captured['temperature'] == 0.5
    assert captured['finish_floor'] == 0.3
    assert captured['supervisor_every_k'] == 7
    assert captured['smoke_early_stop'] is True


def test_when_orchestrate_called_then_run_loop_fn_receives_dev_hard_wall_sec_from_cfg_hard_wall_sec(tmp_path):
    """Pins §7 ralph adapter dev_hard_wall_sec mapping: passes
    cfg.hard_wall_sec straight through (canonical-5-seeds case)."""
    # Arrange
    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        OrchestrateRalphSingleContext,
    )
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.entities.env import Env

    captured: dict = {}

    def fake_run_loop(**kwargs):
        captured.update(kwargs)
        return {
            'iterations': 0,
            'messages': [],
            'finished': False,
            'best_dev_mean': 0.0,
            'body': '',
            'walltime_sec': 0.0,
        }

    adapter = OrchestrateRalphSingleContext(run_loop_fn=fake_run_loop)
    env = Env(tasks_dir=tmp_path, canonical_scorer=FakeCanonicalScorer())
    cfg = BenchConfig(hard_wall_sec=60.0)

    # Act
    list(adapter.orchestrate(env, cfg))

    # Assert
    assert captured['dev_hard_wall_sec'] == 60.0


def test_when_default_run_loop_fn_invoked_without_workspace_then_inner_run_loop_receives_workspace_that_exists():
    """Pins §7 workspace encapsulation: when the wrapper's _fn is
    invoked without a workspace kwarg, it creates a tempdir, threads
    it to the inner loop, and the dir exists at call time."""
    # Arrange
    from pathlib import Path

    from src.reward_bench.adapters.orchestrate_ralph_single_context import (
        default_run_loop_fn,
    )

    captured: dict = {}

    def fake_inner_run_loop(**kwargs):
        ws = kwargs.get('workspace')
        captured['workspace'] = ws
        captured['workspace_exists_during_call'] = (
            ws is not None and Path(ws).exists()
        )
        return {
            'iterations': 0,
            'messages': [],
            'finished': False,
            'best_dev_mean': 0.0,
        }

    fn = default_run_loop_fn(
        _run_loop=fake_inner_run_loop,
        _time_fn=lambda: 0.0,
    )

    # Act
    fn()  # no workspace kwarg

    # Assert
    assert captured['workspace_exists_during_call'] is True
