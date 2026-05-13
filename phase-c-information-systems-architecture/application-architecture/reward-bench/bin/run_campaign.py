"""Campaign run: n_trials=3, max_iters=100, temperature=0.7.

Targets a leaderboard step toward _baks 15.9k. Each trial runs the
full agent loop end-to-end against live qwen3.6-27b-awq.

Total expected walltime: 3 trials x (~2-4 min each) = ~10-15 min."""
import sys
import time

from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.frameworks.main import main
from src.reward_bench.use_cases.run_bench_trials import run_bench_trials


CONFIG = BenchConfig(
    max_iters=100,
    n_trials=3,
    temperature=0.7,
)


def aggregate(trials):
    means = [t.mean_score for t in trials]
    return {
        'n_trials': len(trials),
        'mean_of_means': sum(means) / len(means) if means else 0.0,
        'best_mean': max(means) if means else 0.0,
        'worst_mean': min(means) if means else 0.0,
        'per_trial_mean': means,
        'max_max_tile': max(t.max_max_tile for t in trials),
        'aggregate_walltime_sec': sum(t.aggregate_walltime_sec for t in trials),
    }


if __name__ == '__main__':
    print(f'[campaign] config={CONFIG}', flush=True)
    started = time.monotonic()
    trials = run_bench_trials(
        model_id='qwen3.6-27b-awq',
        config=CONFIG,
        runner=main,
    )
    elapsed = time.monotonic() - started
    agg = aggregate(trials)
    print(f'[campaign] DONE n_trials={agg["n_trials"]} elapsed={elapsed:.1f}s')
    print(f'[campaign] mean_of_means={agg["mean_of_means"]:.1f}')
    print(f'[campaign] best_mean={agg["best_mean"]:.1f}')
    print(f'[campaign] worst_mean={agg["worst_mean"]:.1f}')
    print(f'[campaign] per_trial_mean={agg["per_trial_mean"]}')
    print(f'[campaign] max_max_tile={agg["max_max_tile"]}')
