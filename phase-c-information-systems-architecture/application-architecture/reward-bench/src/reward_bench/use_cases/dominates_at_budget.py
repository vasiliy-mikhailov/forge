"""§7 dominance harness primitive.

Composes Orchestrator.orchestrate with best_score to compare two
orchestrators at the same walltime budget. Returns True iff strong's
best-in-budget score exceeds weak's.
"""
from __future__ import annotations

from src.reward_bench.use_cases.best_score import best_score


def dominates_at_budget(
    strong,
    weak,
    env,
    cfg,
    walltime_budget_sec: float,
) -> bool:
    return (
        best_score(strong.orchestrate(env, cfg), walltime_budget_sec)
        > best_score(weak.orchestrate(env, cfg), walltime_budget_sec)
    )
