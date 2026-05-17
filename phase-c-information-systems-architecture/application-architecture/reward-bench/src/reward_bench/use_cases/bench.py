"""§7 `bench` — top-level composition.

    bench env cfg = argmaxBy (.score) (orchestrate env cfg)

Pure: any IO is the orchestrator's.
"""
from __future__ import annotations

from src.ports.orchestrator import Orchestrator
from src.reward_bench.entities.bench_config import BenchConfig
from src.reward_bench.entities.env import Env
from src.reward_bench.use_cases.best_submission import best_submission
from src.tier1.entities.submission import Submission


def bench(
    orchestrator: Orchestrator,
    env: Env,
    cfg: BenchConfig,
) -> Submission:
    return best_submission(orchestrator.orchestrate(env, cfg))
