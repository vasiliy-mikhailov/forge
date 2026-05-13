"""run_bench_trials: multi-trial bench use case.

See src-spec/reward_bench/use_cases/run_bench_trials/.

Invokes a single-run `runner` (default: main) config.n_trials times.
The closest analogue in the legacy tree is _bak/bin/campaign_tier1.sh's
N_TRIALS loop."""
from typing import Callable, Tuple

from src.reward_bench.entities.bench_config import BenchConfig
from src.tier1.entities.attempt_result import AttemptResult


def run_bench_trials(
    model_id: str,
    config: BenchConfig,
    runner: Callable[..., AttemptResult],
) -> Tuple[AttemptResult, ...]:
    """Run `runner` config.n_trials times and return the AttemptResults."""
    return tuple(
        runner(model_id=model_id, config=config)
        for _ in range(config.n_trials)
    )
