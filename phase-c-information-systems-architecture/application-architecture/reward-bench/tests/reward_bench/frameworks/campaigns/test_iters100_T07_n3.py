"""Campaign test: iters=100, T=0.7, n=3 leaderboard data point.

See tests-spec/reward_bench/frameworks/campaigns/.

Opt-in via `pytest -m campaign`. Runs the 3-trial bench live against
qwen3.6-27b-awq; writes the result to experiments/<date>-<knobs>.json;
asserts the artifact's SHAPE (not specific values — model noise is
real)."""
import json
import math
from dataclasses import asdict
from pathlib import Path

import pytest

from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.frameworks.main import main
from src.reward_bench.use_cases.run_bench_trials import run_bench_trials


REPO = Path(__file__).resolve().parents[4]
ARTIFACT = REPO / 'experiments' / '2026-05-13-iters100-T07-n3.json'
CONFIG = BenchConfig(
    max_iters=100,
    n_trials=3,
    temperature=0.7,
    hard_wall_sec=60.0,  # cycle 26: per-trial scoring cap, ADR 0006 layer 1
)


@pytest.mark.campaign
def test_when_campaign_run_with_iters100_T07_n3_then_artifact_written_with_required_fields():
    # Arrange — config codified above; artifact path declared.
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)

    # Act — run the campaign and serialise the result.
    trials = run_bench_trials(
        model_id='qwen3.6-27b-awq',
        config=CONFIG,
        runner=main,
    )
    per_trial_mean = [t.mean_score for t in trials]
    data = {
        'model_id': 'qwen3.6-27b-awq',
        'config': asdict(CONFIG),
        'n_trials': len(trials),
        'per_trial_mean': per_trial_mean,
        'mean_of_means': sum(per_trial_mean) / len(per_trial_mean),
        'best_mean': max(per_trial_mean),
        'worst_mean': min(per_trial_mean),
        'max_max_tile': max(t.max_max_tile for t in trials),
        'aggregate_walltime_sec': sum(t.aggregate_walltime_sec for t in trials),
    }
    ARTIFACT.write_text(json.dumps(data, indent=2))

    # Assert — shape-only contract.
    assert ARTIFACT.exists()
    loaded = json.loads(ARTIFACT.read_text())
    required = {
        'model_id', 'config', 'n_trials', 'per_trial_mean',
        'mean_of_means', 'best_mean', 'worst_mean',
        'max_max_tile', 'aggregate_walltime_sec',
    }
    assert required <= set(loaded), (
        f'missing required keys: {required - set(loaded)}'
    )
    assert loaded['n_trials'] == 3
    assert len(loaded['per_trial_mean']) == 3
    # Numeric fields finite + non-negative
    for k in ('mean_of_means', 'best_mean', 'worst_mean',
              'aggregate_walltime_sec'):
        v = loaded[k]
        assert isinstance(v, (int, float)) and math.isfinite(v) and v >= 0, (
            f'{k}={v!r} must be finite non-negative number'
        )
    assert isinstance(loaded['max_max_tile'], int)
    assert loaded['max_max_tile'] >= 0
