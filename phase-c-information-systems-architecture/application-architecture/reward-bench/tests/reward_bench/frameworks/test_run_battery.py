"""Cycle 94 / SPEC.md §Make targets: tests for reward-battery driver."""
from __future__ import annotations

import textwrap

import pytest

from src.reward_bench.frameworks.run_battery import (
    load_models,
    run_battery,
    select_battery,
)


# ---------------------------------------------------------------
# select_battery — pure filter function
# ---------------------------------------------------------------

def test_when_battery_filter_applied_then_skipped_models_excluded():
    """select_battery drops `bench_skip: True` entries; preserves order."""
    models = [
        {'id': 'a-1', 'bench_skip': False},
        {'id': 'b-2', 'bench_skip': True},   # SKIP
        {'id': 'c-3'},                       # missing key -> not skipped
        {'id': 'd-4', 'bench_skip': True},   # SKIP
        {'id': 'e-5', 'bench_skip': False},
    ]

    picks = select_battery(models)

    assert [m['id'] for m in picks] == ['a-1', 'c-3', 'e-5'], (
        f'bench_skip filter wrong; got {[m["id"] for m in picks]}'
    )


def test_when_battery_filter_regex_provided_then_narrows_to_matching_ids():
    """Optional regex narrows the selection on the `id` field."""
    models = [
        {'id': 'qwen3.6-27b-fp8', 'bench_skip': False},
        {'id': 'qwen3.6-27b-nvfp4', 'bench_skip': False},
        {'id': 'llama-3.3-70b-nvfp4', 'bench_skip': False},
        {'id': 'gpt-oss-20b', 'bench_skip': False},
        {'id': 'gpt-oss-120b', 'bench_skip': True},  # SKIP even if it matches
    ]

    picks_27b = select_battery(models, filter_regex='27b')
    picks_oss = select_battery(models, filter_regex='gpt-oss')

    assert [m['id'] for m in picks_27b] == [
        'qwen3.6-27b-fp8',
        'qwen3.6-27b-nvfp4',
    ]
    # Regex matches 'gpt-oss-120b' but bench_skip drops it first.
    assert [m['id'] for m in picks_oss] == ['gpt-oss-20b']


# ---------------------------------------------------------------
# run_battery — driver with injected runner
# ---------------------------------------------------------------

def _write_yml(path, text: str):
    path.write_text(textwrap.dedent(text).lstrip())


def test_when_run_battery_called_then_runner_invoked_per_non_skipped_model(tmp_path):
    """run_battery calls `runner` once per non-skipped model, returns tuples."""
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: alpha
            bench_skip: false
          - id: beta
            bench_skip: true
          - id: gamma
            bench_skip: false
    """)
    calls: list[str] = []
    def recorder(model_id: str) -> int:
        calls.append(model_id)
        return 0

    results = run_battery(
        tier=1, task='2048', registry_path=yml, runner=recorder,
    )

    assert calls == ['alpha', 'gamma'], f'recorder calls: {calls}'
    assert results == [('alpha', 0), ('gamma', 0)], f'results: {results}'


def test_when_run_battery_runner_returns_mixed_rc_then_all_calls_still_made(tmp_path):
    """A non-zero rc on one model does NOT short-circuit the battery."""
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: a
            bench_skip: false
          - id: b
            bench_skip: false
          - id: c
            bench_skip: false
    """)
    calls: list[str] = []
    def recorder(model_id: str) -> int:
        calls.append(model_id)
        return 2 if model_id == 'b' else 0  # b fails

    results = run_battery(
        tier=1, task='2048', registry_path=yml, runner=recorder,
    )

    assert calls == ['a', 'b', 'c'], 'all three must be attempted'
    assert results == [('a', 0), ('b', 2), ('c', 0)]


def test_when_run_battery_filter_regex_then_only_matching_models_run(tmp_path):
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: qwen-27b
            bench_skip: false
          - id: qwen-32b
            bench_skip: false
          - id: llama-70b
            bench_skip: false
    """)
    calls: list[str] = []
    def recorder(mid: str) -> int:
        calls.append(mid)
        return 0

    run_battery(
        tier=1, task='2048', registry_path=yml,
        filter_regex='qwen', runner=recorder,
    )

    assert calls == ['qwen-27b', 'qwen-32b']


# ---------------------------------------------------------------
# load_models — yaml reader sanity
# ---------------------------------------------------------------

def test_when_load_models_called_then_returns_yaml_list(tmp_path):
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        models:
          - id: foo
          - id: bar
    """)
    out = load_models(yml)
    assert isinstance(out, list)
    assert [m['id'] for m in out] == ['foo', 'bar']


def test_when_load_models_missing_top_key_then_value_error(tmp_path):
    yml = tmp_path / 'models.yml'
    _write_yml(yml, """
        other_key: []
    """)
    with pytest.raises(ValueError, match='models'):
        load_models(yml)
