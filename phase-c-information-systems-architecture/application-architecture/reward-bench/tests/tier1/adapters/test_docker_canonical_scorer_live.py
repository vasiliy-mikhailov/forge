"""Cycle 123: CanonicalScorerPort live-runtime test per cycle 122.

Actually invokes `docker run reward-bench-tier1:0.4` against a trivial
Solver body and asserts the returned AttemptResult has the expected
shape (n_games matches seed count; final_states are valid sentinels;
mean_score is a finite non-negative number).

This is the test cycle 122 says every runtime-boundary Port MUST
have. Without it, image-missing / runner-broken / Docker-flag-wrong
bugs ship silently to the canonical bench (as cycle 105 demonstrated).

@pytest.mark.live — opt-in via `pytest -m live`. Skipped by the
default TIA gate. Setup restarts vLLM via the conftest model_client
autouse fixture (expected; live tests are allowed to wipe out a
concurrent production-runtime bench).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.tier1.adapters.docker_canonical_scorer import DockerCanonicalScorer


REPO = Path(__file__).resolve().parents[3]
ENV_PATH = REPO / "tasks" / "2048" / "env.py"


_TRIVIAL_SOLVER = """\
import transitions  # required by submission protocol


class Solver:
    def move(self, board):
        # Trivial: always swipe West. Will hit max_moves or lose quickly;
        # the test only cares that the runner produces a real GameResult,
        # not that the solver is good.
        return 'W'
"""


@pytest.mark.live
def test_when_score_invoked_with_trivial_solver_then_returns_real_attempt_result(
    tmp_path,
):
    # Arrange — trivial submission body + real DockerCanonicalScorer.
    sub_path = tmp_path / "submission.py"
    sub_path.write_text(_TRIVIAL_SOLVER)
    reports_dir = tmp_path / "reports"

    scorer = DockerCanonicalScorer(env_path=ENV_PATH)

    # Act — really run docker; live config (3 seeds, 60s aggregate cap
    # per cycle-122 LIVE_CONFIG conventions).
    seeds = (1, 2, 3)
    result = scorer.score(
        sub_path, seeds,
        hard_wall_sec=60.0,
        reports_root=reports_dir,
    )

    # Assert — real AttemptResult shape.
    assert result.n_games == 3, (
        f"expected 3 games, got {result.n_games}; states "
        f"{[g.final_state for g in result.games]}"
    )

    # final_state must be a valid sentinel (not a typo, not None).
    VALID_STATES = {
        "won", "lost", "max_moves", "stagnated",
        "walltime_exceeded", "solver_error", "invalid_action",
        "protocol_violation",
    }
    for g in result.games:
        assert g.final_state in VALID_STATES, (
            f"seed {g.seed}: unknown final_state {g.final_state!r}"
        )

    # mean_score is finite + non-negative (trivial solver may score 0;
    # never negative; never NaN).
    assert result.mean_score >= 0.0
    assert result.mean_score == result.mean_score   # NaN check

    # max_max_tile is at least 2 (the initial board has tile 2;
    # any played game has at least that).
    assert result.max_max_tile >= 2

    # The trivial solver should NOT all-walltime-fail in 60s for 3
    # seeds — that's the cycle-121 sentinel pattern indicating
    # infrastructure failure. Catch it explicitly:
    n_walltime = sum(1 for g in result.games
                     if g.final_state == "walltime_exceeded")
    assert n_walltime < 3, (
        f"all 3 games walltime_exceeded in <60s — likely Docker "
        f"infrastructure failure (image missing? daemon down? "
        f"runner broken?). aggregate_walltime_sec={result.aggregate_walltime_sec:.1f}s"
    )
