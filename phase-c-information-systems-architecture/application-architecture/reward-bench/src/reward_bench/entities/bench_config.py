"""BenchConfig: orchestrator-side knob panel for a bench run.

See src-spec/reward_bench/entities/bench_config/.

Defaults are codified in
reward-bench/docs/adr/0003-bench-defaults-500-iters-10-trials-temp-0.7.md.

hard_wall_sec added in cycle 24 per
reward-bench/docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md
layer 1 — the input-knob counterpart to score_submission's cap and to
AttemptResult's output observation field."""
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchConfig:
    """Frozen tuning knobs for a bench run. See ADRs 0003 + 0006."""

    max_iters: int = 500
    n_trials: int = 10
    temperature: float = 0.7
    max_no_improve: int = 999999
    finish_floor: float = 0.0
    hard_wall_sec: float = 0.0
    supervisor_every_k: int = 0  # cycle 35: ADR 0005 cadence; 0 = disabled
