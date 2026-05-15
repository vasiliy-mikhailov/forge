"""Cycle 102: contract tests for the resumable canonical battery."""
from __future__ import annotations

import json
import textwrap

import pytest

from src.reward_bench.frameworks.run_battery import (
    canonical_artifact_path,
    run_canonical_battery,
)


def _write_yml(path, text: str):
    path.write_text(textwrap.dedent(text).lstrip())


def test_when_canonical_battery_runs_with_no_artifacts_then_runner_invoked_per_trial(tmp_path):
    """No artifacts -> every (model, trial) runs."""
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: a
            bench_skip: false
          - id: b
            bench_skip: false
    """)
    calls: list[tuple[str, int]] = []
    def recorder(model_id: str, trial: int) -> dict:
        calls.append((model_id, trial))
        return {'model_id': model_id, 'trial': trial,
                'mean_score': 100.0, 'median_score': 100.0,
                'std_score': 0.0, 'max_max_tile': 16, 'n_games': 20,
                'aggregate_walltime_sec': 1.0, 'best_dev_mean': 50.0,
                'games': []}

    run_canonical_battery(
        n_trials=3, registry_path=yml,
        experiments_root=tmp_path / 'exp', runner=recorder,
    )

    # 2 models × 3 trials = 6 invocations.
    assert calls == [
        ('a', 0), ('a', 1), ('a', 2),
        ('b', 0), ('b', 1), ('b', 2),
    ], f'unexpected runner sequence: {calls}'


def test_when_canonical_battery_resumes_then_existing_artifacts_skip(tmp_path):
    """Existing artifacts -> runner NOT called for those (model, trial)."""
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: alpha
            bench_skip: false
          - id: beta
            bench_skip: false
    """)
    exp = tmp_path / 'exp'
    exp.mkdir()

    # Pre-create artifacts for alpha trials 0+1 and beta trial 0.
    for mid, trial in [('alpha', 0), ('alpha', 1), ('beta', 0)]:
        path = canonical_artifact_path(mid, trial, experiments_root=exp)
        path.write_text(json.dumps({'model_id': mid, 'trial': trial,
                                    'mean_score': 1.0}))

    calls: list[tuple[str, int]] = []
    def recorder(model_id: str, trial: int) -> dict:
        calls.append((model_id, trial))
        return {'model_id': model_id, 'trial': trial, 'mean_score': 2.0,
                'median_score': 2.0, 'std_score': 0.0,
                'max_max_tile': 16, 'n_games': 20,
                'aggregate_walltime_sec': 1.0, 'best_dev_mean': 1.0,
                'games': []}

    run_canonical_battery(
        n_trials=3, registry_path=yml,
        experiments_root=exp, runner=recorder,
    )

    # Only the 3 missing trials should have been invoked.
    assert calls == [('alpha', 2), ('beta', 1), ('beta', 2)], (
        f'expected to skip pre-existing; got runs: {calls}'
    )


def test_when_canonical_battery_runner_raises_keyboard_interrupt_then_no_artifact(tmp_path):
    """Ctrl-C mid-run -> the interrupted (model, trial) artifact is NOT
    written. On resume, that trial is re-attempted."""
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: only
            bench_skip: false
    """)
    exp = tmp_path / 'exp'

    def recorder_raises(model_id: str, trial: int):
        raise KeyboardInterrupt('user pressed Ctrl-C')

    with pytest.raises(KeyboardInterrupt):
        run_canonical_battery(
            n_trials=2, registry_path=yml,
            experiments_root=exp, runner=recorder_raises,
        )

    # No artifact written for the trial that was interrupted.
    assert not canonical_artifact_path('only', 0, experiments_root=exp).exists()


def test_when_canonical_battery_completes_a_trial_then_artifact_written(tmp_path):
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: foo
            bench_skip: false
    """)
    exp = tmp_path / 'exp'

    def recorder(model_id: str, trial: int) -> dict:
        return {'model_id': model_id, 'trial': trial, 'mean_score': 42.0,
                'median_score': 42.0, 'std_score': 0.0,
                'max_max_tile': 128, 'n_games': 20,
                'aggregate_walltime_sec': 60.0, 'best_dev_mean': 21.0,
                'games': []}

    run_canonical_battery(
        n_trials=1, registry_path=yml,
        experiments_root=exp, runner=recorder,
    )

    p = canonical_artifact_path('foo', 0, experiments_root=exp)
    assert p.exists(), f'artifact not written: {p}'
    data = json.loads(p.read_text())
    assert data['mean_score'] == 42.0
    assert data['trial'] == 0


def test_when_canonical_battery_filter_regex_then_only_matching_models_run(tmp_path):
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: qwen-27b
            bench_skip: false
          - id: llama-70b
            bench_skip: false
    """)
    calls: list[str] = []
    def recorder(model_id, trial):
        calls.append(model_id)
        return {'model_id': model_id, 'trial': trial, 'mean_score': 1.0,
                'median_score': 1.0, 'std_score': 0.0, 'max_max_tile': 8,
                'n_games': 20, 'aggregate_walltime_sec': 1.0,
                'best_dev_mean': 0.5, 'games': []}

    run_canonical_battery(
        n_trials=1, registry_path=yml,
        experiments_root=tmp_path / 'exp', filter_regex='qwen',
        runner=recorder,
    )

    assert calls == ['qwen-27b']
