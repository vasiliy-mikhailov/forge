"""BenchConfig: orchestrator-side knob panel for a bench run.

See src-spec/reward_bench/entities/bench_config/.

Defaults are codified in
reward-bench/docs/adr/0003-bench-defaults-500-iters-10-trials-temp-0.7.md."""
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchConfig:
    """Frozen tuning knobs for a bench run. See ADR 0003 for defaults."""

    max_iters: int = 500
    n_trials: int = 10
    temperature: float = 0.7
    max_no_improve: int = 999999
    finish_floor: float = 0.0
