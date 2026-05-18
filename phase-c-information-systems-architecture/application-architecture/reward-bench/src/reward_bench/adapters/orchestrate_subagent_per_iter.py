"""§2 OrchestrateSubagentPerIter — three-role orchestrator.

Per SOLUTION-ARCHITECTURE.md §2: thin loop over (build snapshot,
ask generator, score body, yield Submission). Holds no model
context; cumulative state lives in process memory as the running
best and the tuple of prior submissions.

Each iter's snapshot reflects what the orchestrator knows from
iters 1..k-1 — fresh per-iter context, no token carry-over. The
task description (`env_spec`) comes from `env.env_spec`, set once
by the env_factory. The per-iter wallclock budget
(`time_remaining_sec`) comes from `cfg.hard_wall_sec` — the §4
SolutionGenerator runtime enforces it.
"""
from __future__ import annotations

from typing import Iterable

from src.reward_bench.entities.context_snapshot import ContextSnapshot
from src.tier1.entities.submission import Submission


_BASELINE = Submission(body='', score=0.0, walltime_sec=0.0)


class OrchestrateSubagentPerIter:
    def __init__(self, solution_generator, runner):
        self._gen = solution_generator
        self._runner = runner

    def orchestrate(self, env, cfg) -> Iterable[Submission]:
        history: list[Submission] = []
        best = _BASELINE
        for _ in range(cfg.max_iters):
            snapshot = ContextSnapshot(
                env_spec=env.env_spec,
                best_so_far=best,
                history_digest=tuple(history),
                iters_remaining=cfg.max_iters,
                time_remaining_sec=cfg.hard_wall_sec,
                budget_sec_per_seed=0.0,
            )
            body = self._gen.generate(snapshot)
            attempt = self._runner.score_body(
                body, (), hard_wall_sec=cfg.hard_wall_sec,
            )
            sub = Submission(
                body=body,
                score=attempt.mean_score,
                walltime_sec=attempt.aggregate_walltime_sec,
            )
            history.append(sub)
            if sub.score > best.score:
                best = sub
            yield sub
