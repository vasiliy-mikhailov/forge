"""§7 ralph-single-context Orchestrator adapter + production wrapper.

The adapter wraps `src.tier1.agent_loop.run_loop` (via a `run_loop_fn`
seam) and re-shapes its dict return into `Submission` value objects
for the bench. `run_loop_with_metrics` closes the contract gap
between the real run_loop (which produces no walltime / body) and
the adapter. `default_run_loop_fn` is the production factory that
binds real defaults.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from src.tier1.entities.submission import Submission


class OrchestrateRalphSingleContext:
    def __init__(self, run_loop_fn=None):
        if run_loop_fn is None:
            from src.tier1.agent_loop import run_loop as _rl
            run_loop_fn = _rl
        self._run_loop = run_loop_fn

    def orchestrate(self, env, cfg) -> Iterable[Submission]:
        result = self._run_loop(
            tasks_dir=env.tasks_dir,
            max_iters=cfg.max_iters,
            temperature=cfg.temperature,
            finish_floor=cfg.finish_floor,
            supervisor_every_k=cfg.supervisor_every_k,
            smoke_early_stop=cfg.smoke_early_stop,
            dev_hard_wall_sec=cfg.hard_wall_sec,
        )
        yield Submission(
            body=result['body'],
            score=result['best_dev_mean'],
            walltime_sec=result['walltime_sec'],
        )


def run_loop_with_metrics(
    *,
    _run_loop=None,
    _time_fn=None,
    _body_reader=None,
    **kwargs,
) -> dict:
    import time as _time
    if _run_loop is None:
        from src.tier1.agent_loop import run_loop as _rl
        _run_loop = _rl
    if _time_fn is None:
        _time_fn = _time.monotonic

    t0 = _time_fn()
    result = _run_loop(**kwargs)
    t1 = _time_fn()
    result['walltime_sec'] = t1 - t0
    if _body_reader is not None:
        result['body'] = _body_reader(kwargs['workspace'])
    return result


def _default_body_reader(workspace) -> str:
    p = Path(workspace) / 'submission.best.py'
    return p.read_text() if p.exists() else ''


def default_run_loop_fn(*, _run_loop=None, _time_fn=None, _body_reader=None):
    if _body_reader is None:
        _body_reader = _default_body_reader

    def _fn(**kwargs):
        if 'tasks_dir' in kwargs and 'env_dir' not in kwargs:
            kwargs['env_dir'] = Path(kwargs['tasks_dir']).parent
        if 'workspace' in kwargs:
            return run_loop_with_metrics(
                _run_loop=_run_loop,
                _time_fn=_time_fn,
                _body_reader=_body_reader,
                **kwargs,
            )
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            return run_loop_with_metrics(
                _run_loop=_run_loop,
                _time_fn=_time_fn,
                _body_reader=_body_reader,
                workspace=td,
                **kwargs,
            )
    return _fn
