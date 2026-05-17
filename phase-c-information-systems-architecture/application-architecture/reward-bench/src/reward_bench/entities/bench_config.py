"""BenchConfig: orchestrator-side knob panel for a bench run."""
from dataclasses import dataclass


@dataclass(frozen=True)
class BenchConfig:
    """Frozen tuning knobs for a bench run."""

    max_iters: int = 500
    n_trials: int = 10
    temperature: float = 0.7
    max_no_improve: int = 999999
    finish_floor: float = 0.0
    hard_wall_sec: float = 0.0
    supervisor_every_k: int = 0
    # When True, bench forces finished=True on first execute_submission
    # observation with dev_mean > 0.
    smoke_early_stop: bool = False
