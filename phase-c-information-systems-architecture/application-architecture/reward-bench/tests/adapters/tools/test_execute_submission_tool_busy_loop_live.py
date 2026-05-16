"""Cycle 128 RED: ExecuteSubmissionTool must hard-kill CPU-bound solvers.

Adversarial busy-loop solver — pure-Python C-level work (no sleep,
no I/O). Pre-cycle-128 dev runner uses score_submission with daemon-
thread soft timeout that doesn't actually interrupt C-level work;
test wedges. Cycle-128 fix switches dev runner to DockerCanonicalScorer
which hard-kills via Docker --pids-limit + cgroup quotas.

@pytest.mark.live — opt-in. Hard-timeout via pytest-timeout plugin
so a wedge doesn't freeze CI.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.adapters.tools.execute_submission_tool import ExecuteSubmissionTool


REPO = Path(__file__).resolve().parents[3]
TASKS_DIR = REPO / "tasks" / "2048"


# Adversarial: pure-Python busy loop. No sleep, no I/O, no yield.
# Pre-cycle-128 dev runner cannot interrupt this with a soft timeout.
_BUSY_LOOP_SOLVER = """\
from transitions import Machine
import time

class Solver:
    def move(self, board):
        # Burn pure-Python CPU for 60 wall-seconds, never yielding to
        # the dev runner\'s daemon-thread soft timeout.
        end = time.monotonic() + 60.0
        x = 1.0
        while time.monotonic() < end:
            x = x * 1.5 + 1.0
            if x > 1e100:
                x = 1.0
        return \'W\'
"""


@pytest.mark.live
@pytest.mark.timeout(180)   # hard cap: test must NOT wedge >2 min
def test_when_execute_submission_dispatched_with_busy_loop_solver_then_returns_within_dev_hard_wall_sec(
    tmp_path,
):
    # Arrange — adversarial submission + real ExecuteSubmissionTool.
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "submission.py").write_text(_BUSY_LOOP_SOLVER)

    tool = ExecuteSubmissionTool()
    ctx = {
        "workspace": workspace,
        "env_dir": TASKS_DIR,
        "tasks_dir": TASKS_DIR,
        "dev_hard_wall_sec": 30.0,   # tight budget
    }

    # Act — measure wall time of the dispatch.
    t0 = time.monotonic()
    obs_str = tool.dispatch({"content": _BUSY_LOOP_SOLVER}, ctx)
    elapsed = time.monotonic() - t0

    # Assert: returned in bounded time, not forever.
    # dev_hard_wall_sec=30s; DockerCanonicalScorer subprocess.run
    # timeout is hard_wall_sec + 30s grace = 60s. Direct call: 60s.
    # Via _execute_submission wrapper: ~120s (extra ~60s wrapper
    # overhead — separate concern). Pre-cycle-128 bench wedged for
    # 10+ minutes and counting. Threshold 150s gives margin while
    # proving no-wedge.
    assert elapsed < 150.0, (
        f"execute_submission did not return within 150s; took {elapsed:.1f}s — "
        f"dev runner wedged on busy-loop solver. Cycle-128 fix not in place?"
    )

    # Parse the observation.
    payload = obs_str[len("<observation>"): -len("</observation>")]
    obs = json.loads(payload)

    # The busy-loop solver burns through dev_hard_wall_sec without
    # making any 2048 moves. The dev runner should mark every dev
    # seed as walltime_exceeded (sentinel per ADR 0006 + the
    # cycle-23/27 walltime sentinel pattern).
    per_seed = obs.get("per_seed") or []
    assert len(per_seed) > 0, (
        f"no per_seed entries; observation: {obs!r}"
    )

    # Every seed should be walltime_exceeded (or at minimum, none
    # should report success since the solver never makes a real move).
    states = {g.get("state") for g in per_seed}
    assert states.issubset({"walltime_exceeded", "stagnated", "solver_error"}), (
        f"unexpected final_states for busy-loop solver: {states}; "
        f"per_seed={per_seed!r}"
    )
