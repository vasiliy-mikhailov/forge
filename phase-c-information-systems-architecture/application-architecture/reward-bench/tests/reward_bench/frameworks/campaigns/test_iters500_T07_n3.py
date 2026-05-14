"""Cycle 37 campaign: iters500 / n_trials=3 / T=0.7 / supervisor_every_k=20.

See tests-spec/reward_bench/frameworks/campaigns/test_spec_when_campaign_run_with_iters500_T07_n3_*.md."""
import json
from pathlib import Path

import pytest

from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.frameworks.main import main
from src.reward_bench.use_cases.run_bench_trials import run_bench_trials


REPO = Path(__file__).resolve().parents[4]
ARTIFACT = REPO / 'experiments' / '2026-05-14-iters500-T07-n3.json'
CONFIG = BenchConfig(
    max_iters=500,
    n_trials=3,
    temperature=0.7,
    hard_wall_sec=120.0,
    supervisor_every_k=20,
)


@pytest.mark.campaign
def test_when_campaign_run_with_iters500_T07_n3_then_artifact_written_with_required_fields():
    """Live campaign — chases _bak's 15920 with bigger budget."""
    # Act
    trials = run_bench_trials(
        runner=main, model_id='qwen3.6-27b-awq', config=CONFIG,
    )

    # Aggregate
    per_trial_mean = [t.mean_score for t in trials]
    mean_of_means = sum(per_trial_mean) / len(per_trial_mean)
    best_mean = max(per_trial_mean)
    worst_mean = min(per_trial_mean)
    max_max_tile = max(t.max_max_tile for t in trials)
    aggregate_walltime_sec = sum(t.aggregate_walltime_sec for t in trials)

    payload = {
        'model_id': 'qwen3.6-27b-awq',
        'config': {
            'max_iters': CONFIG.max_iters,
            'n_trials': CONFIG.n_trials,
            'temperature': CONFIG.temperature,
            'max_no_improve': CONFIG.max_no_improve,
            'finish_floor': CONFIG.finish_floor,
            'hard_wall_sec': CONFIG.hard_wall_sec,
            'supervisor_every_k': CONFIG.supervisor_every_k,
        },
        'n_trials': len(trials),
        'per_trial_mean': per_trial_mean,
        'mean_of_means': mean_of_means,
        'best_mean': best_mean,
        'worst_mean': worst_mean,
        'max_max_tile': max_max_tile,
        'aggregate_walltime_sec': aggregate_walltime_sec,
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(payload, indent=2))

    # Shape assertions
    assert ARTIFACT.exists()
    on_disk = json.loads(ARTIFACT.read_text())
    for key in (
        'model_id', 'config', 'n_trials', 'per_trial_mean',
        'mean_of_means', 'best_mean', 'worst_mean', 'max_max_tile',
        'aggregate_walltime_sec',
    ):
        assert key in on_disk, f'missing key {key}'
    assert len(on_disk['per_trial_mean']) == 3
    for k in ('mean_of_means', 'best_mean', 'worst_mean',
              'aggregate_walltime_sec', 'max_max_tile'):
        v = on_disk[k]
        assert v == v  # not NaN
        assert v >= 0
