"""§2 OrchestrateSubagentPerIter — three-role orchestrator.

Per SOLUTION-ARCHITECTURE.md §2: thin loop over (build snapshot,
ask generator, score body, yield Submission). Holds no model
context; cumulative state lives in process memory.
"""
from __future__ import annotations

from typing import Iterable

from src.reward_bench.entities.context_snapshot import ContextSnapshot
from src.tier1.entities.submission import Submission


class OrchestrateSubagentPerIter:
    def __init__(self, solution_generator, runner):
        self._gen = solution_generator
        self._runner = runner

    def orchestrate(self, env, cfg) -> Iterable[Submission]:
        for _ in range(cfg.max_iters):
            snapshot = ContextSnapshot(
                env_spec='',
                best_so_far=Submission(body='', score=0.0, walltime_sec=0.0),
                history_digest=(),
                iters_remaining=cfg.max_iters,
                time_remaining_sec=0.0,
                budget_sec_per_seed=0.0,
            )
            body = self._gen.generate(snapshot)
            attempt = self._runner.score_body(
                body, (), hard_wall_sec=cfg.hard_wall_sec,
            )
            yield Submission(
                body=body,
                score=attempt.mean_score,
                walltime_sec=attempt.aggregate_walltime_sec,
            )
