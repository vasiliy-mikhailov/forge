"""§7 ralph-single-context Orchestrator adapter.

Wraps `src.tier1.agent_loop.run_loop` and re-shapes its dict return
into `Submission` value objects for the bench.
"""
from __future__ import annotations

from typing import Iterable

from src.tier1.entities.submission import Submission


class OrchestrateRalphSingleContext:
    def __init__(self, run_loop_fn=None):
        if run_loop_fn is None:
            from src.tier1.agent_loop import run_loop as _rl
            run_loop_fn = _rl
        self._run_loop = run_loop_fn

    def orchestrate(self, env, cfg) -> Iterable[Submission]:
        result = self._run_loop()
        yield Submission(
            body=result['body'],
            score=result['best_dev_mean'],
            walltime_sec=0.0,
        )
