"""Cycle 125: ExecuteSubmissionTool live-runtime test per cycle 122.

Actually invokes ExecuteSubmissionTool.dispatch against the dev
sandbox per ADR 0008 — writes a trivial Solver body to /workspace,
runs in Docker (image bumped via _execute_submission), parses the
returned JSON observation.

@pytest.mark.live — opt-in via `pytest -m live`. Setup may restart
vLLM via conftest model_client fixture (expected per user
clarification).

view + finish are pure-Python and opt out of the live runtime
(cycle-122 scale-invariant exception); their unit tests in
tests/adapters/test_tier1_tool_registry.py already pin behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.adapters.tools.execute_submission_tool import ExecuteSubmissionTool


REPO = Path(__file__).resolve().parents[3]
TASKS_DIR = REPO / "tasks" / "2048"


_TRIVIAL_SOLVER = """\
from transitions import Machine


class Solver:
    def move(self, board):
        return 'W'
"""


@pytest.mark.live
def test_when_execute_submission_dispatched_with_trivial_solver_then_returns_real_observation(
    tmp_path,
):
    # Arrange — trivial submission body + real ExecuteSubmissionTool.
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "submission.py").write_text(_TRIVIAL_SOLVER)

    tool = ExecuteSubmissionTool()
    ctx = {
        "workspace": workspace,
        "env_dir": TASKS_DIR,
        "tasks_dir": TASKS_DIR,
        "dev_hard_wall_sec": 60.0,
    }

    # Act — really run the dev sandbox (Docker per ADR 0008).
    obs_str = tool.dispatch({"content": _TRIVIAL_SOLVER}, ctx)

    # Assert — observation is `<observation>{json...}</observation>`.
    assert isinstance(obs_str, str), f"obs must be str, got {type(obs_str)}"
    assert obs_str.startswith("<observation>") and obs_str.endswith("</observation>"), (
        f"observation must be wrapped in <observation>...</observation>; got: {obs_str[:200]!r}"
    )
    payload = obs_str[len("<observation>"): -len("</observation>")]
    obs = json.loads(payload)
    assert isinstance(obs, dict), f"obs must be dict, got {type(obs)}"

    # Per cycle-119 src_spec: per_seed, protocol_violations, mean,
    # max_tile_best, walltime_sec_total.
    for key in ("per_seed", "mean", "walltime_sec_total"):
        assert key in obs, f"observation missing key {key!r}; got keys {list(obs)}"

    # per_seed is a non-empty list.
    assert isinstance(obs["per_seed"], list)
    assert len(obs["per_seed"]) > 0

    # The trivial solver doesn't cause protocol violations — if it
    # did, the dev_runner pipeline is broken (cycle-123-style).
    pv = obs.get("protocol_violations") or []
    assert pv == [], (
        f"trivial Solver should produce zero protocol violations; "
        f"got {pv} — dev_runner / Docker / submission pipeline broken?"
    )

    # walltime_sec_total > 0 — if 0.0, the runner never actually ran
    # (instant-fail fingerprint, like cycle 123's discovery).
    assert obs["walltime_sec_total"] > 0.0, (
        f"walltime_sec_total=0 — dev runner never executed? "
        f"obs={obs!r}"
    )
