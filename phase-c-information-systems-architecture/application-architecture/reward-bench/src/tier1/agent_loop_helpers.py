"""Pure helpers extracted from `run_loop`'s in-loop state machine.

Each function is a pure transition over the loop's progress state —
no I/O, no time, no globals. The orchestrator (`run_loop`) wires
these together with the impure edges (model call, tool dispatch,
file write).
"""
from __future__ import annotations


def reject_finish_for_floor(
    finish_floor: float,
    best_dev_mean: float | None,
) -> str | None:
    """Return an `<error>finish rejected: ...</error>` observation
    string if `finish_floor > 0` AND the best observed dev_mean is
    below the floor; otherwise None (allow the finish).

    `best_dev_mean=None` (no dev_runner observation yet) counts as
    below-floor.
    """
    if finish_floor <= 0:
        return None
    if best_dev_mean is not None and best_dev_mean >= finish_floor:
        return None
    best_str = (str(best_dev_mean) if best_dev_mean is not None
                else 'unknown (no dev_runner yet)')
    return (
        f'<error>finish rejected: best dev MEAN so far is '
        f'{best_str}, which is below the finish_floor '
        f'({finish_floor}). You must produce a submission '
        f'scoring above this floor before finishing. '
        f'Run `bash python3 /tasks/2048/dev_runner.py '
        f'/workspace/submission.py` to test, then refine '
        f'your FSM until dev MEAN exceeds {finish_floor}.'
        f'</error>'
    )


def update_best_snapshot(
    current_best: float | None,
    new_mean: float,
) -> tuple[float, bool]:
    """Return (new_best, snapshot_should_fire). If `new_mean` is
    strictly greater than `current_best` (or `current_best is None`),
    the snapshot fires and `new_best == new_mean`. Otherwise
    `new_best == current_best` and snapshot does not fire.
    """
    if current_best is None or new_mean > current_best:
        return (new_mean, True)
    return (current_best, False)


def sweep_sample(
    iter_n: int,
    parsed: tuple[float, int, float] | None,
) -> tuple[int, float, int, float]:
    """Convert a parsed dev_runner observation (mean, max_tile,
    walltime) into a supervisor sweep `Sample` tuple. `None` becomes
    the zero-filled placeholder `(iter_n, 0.0, 0, 0.0)`.
    """
    if parsed is None:
        return (iter_n, 0.0, 0, 0.0)
    mean, max_tile, walltime = parsed
    return (iter_n, mean, max_tile, walltime)


def should_smoke_stop(
    smoke_early_stop: bool,
    best_dev_mean: float | None,
) -> bool:
    """True iff smoke mode is enabled AND the best observed dev_mean
    is strictly positive. Pure boolean — no time-since-last logic
    here; the loop owns the iter cadence.
    """
    return bool(smoke_early_stop) and best_dev_mean is not None and best_dev_mean > 0


def promote_body_text(body: str) -> str:
    """Ensure the submission body ends with exactly one trailing
    newline before it's written to disk. The fenced-block parser
    strips the final newline; we restore it for PEP-8 conformance.
    """
    return body if body.endswith('\n') else body + '\n'
