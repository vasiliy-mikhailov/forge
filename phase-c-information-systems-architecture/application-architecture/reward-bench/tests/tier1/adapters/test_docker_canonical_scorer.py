"""Cycle 105 sub-B: contract tests for DockerCanonicalScorer adapter.

Tests stub subprocess.run with a fake that writes a result.json to the
mounted reports dir. No real Docker spawn — these tests run fully
offline in the fast gate.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.adapters.multiprocessing_cpu_count import FixedCpuCount
from src.tier1.adapters.docker_canonical_scorer import (
    DockerCanonicalScorer,
    _DEFAULT_IMAGE,
)


def _make_fake_docker(reports_dir: Path, *, summary: dict | None = None,
                     returncode: int = 0):
    """Returns a fake subprocess.run that writes summary to reports_dir.

    summary defaults to a 2-seed happy-path result.
    """
    payload = summary or {
        "games": [
            {"seed": 1000, "score": 1000, "max_tile": 64, "moves": 100,
             "final_state": "lost", "walltime_sec": 12.3},
            {"seed": 1001, "score": 500, "max_tile": 32, "moves": 80,
             "final_state": "lost", "walltime_sec": 8.1},
        ],
        "n_games": 2, "mean_score": 750.0, "median_score": 750,
        "min_score": 500, "max_score": 1000, "max_max_tile": 64,
        "aggregate_walltime_sec": 20.4, "stagnation_sec": 60,
        "hard_wall_sec": 300, "walltime_exceeded": False,
        "stagnated_any": False, "n_workers": 12,
    }
    captured = {"cmd": None}

    def fake_run(cmd, capture_output=True, text=True, timeout=None):
        captured["cmd"] = cmd
        # Find the reports mount in the docker command and write result.json.
        for i, a in enumerate(cmd):
            if a == "-v" and i + 1 < len(cmd):
                m = cmd[i + 1]
                if ":/reports" in m:
                    host_dir = m.split(":/reports")[0]
                    (Path(host_dir) / "result.json").write_text(json.dumps(payload))
                    break
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr="")

    return fake_run, captured


@pytest.mark.no_fake
def test_when_score_invoked_then_result_json_parsed_into_attempt_result(monkeypatch, tmp_path):
    """ADR 0006 Layer 2: container's result.json maps cleanly to AttemptResult."""
    sub = tmp_path / "submission.py"; sub.write_text("class Solver: ...")
    reports = tmp_path / "reports"

    fake_run, _ = _make_fake_docker(reports)
    monkeypatch.setattr(subprocess, "run", fake_run)

    scorer = DockerCanonicalScorer(cpu_count_port=FixedCpuCount(24))
    result = scorer._score_path(sub, seeds=(1000, 1001),
                          hard_wall_sec=300.0, reports_root=reports)

    assert result.n_games == 2
    assert result.mean_score == 750.0
    assert result.max_max_tile == 64
    assert len(result.games) == 2
    assert result.games[0].seed == 1000
    assert result.games[0].score == 1000
    assert result.games[1].seed == 1001
    assert result.games[1].score == 500


@pytest.mark.no_fake
def test_when_result_json_missing_then_walltime_exceeded_sentinels(monkeypatch, tmp_path):
    """If container crashed before writing result.json, all seeds get
    walltime_exceeded sentinels (defensive)."""
    sub = tmp_path / "submission.py"; sub.write_text("class Solver: ...")
    reports = tmp_path / "reports"

    def fake_run(cmd, **_):
        # Don't write result.json.
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="crash")
    monkeypatch.setattr(subprocess, "run", fake_run)

    scorer = DockerCanonicalScorer(cpu_count_port=FixedCpuCount(8))
    result = scorer._score_path(sub, seeds=(1, 2, 3),
                          hard_wall_sec=300.0, reports_root=reports)

    assert result.n_games == 3
    assert all(g.final_state == "walltime_exceeded" for g in result.games)
    assert result.walltime_exceeded is True


@pytest.mark.no_fake
def test_when_outer_timeout_fires_then_walltime_exceeded_sentinels(monkeypatch, tmp_path):
    """If subprocess.run raises TimeoutExpired (container exceeded the
    outer grace period), all seeds get walltime_exceeded sentinels."""
    sub = tmp_path / "submission.py"; sub.write_text("class Solver: ...")
    reports = tmp_path / "reports"

    def fake_run(cmd, **_):
        raise subprocess.TimeoutExpired(cmd, timeout=30)
    monkeypatch.setattr(subprocess, "run", fake_run)

    scorer = DockerCanonicalScorer(cpu_count_port=FixedCpuCount(8))
    result = scorer._score_path(sub, seeds=(1, 2),
                          hard_wall_sec=10.0, reports_root=reports)
    assert result.walltime_exceeded is True


@pytest.mark.no_fake
def test_when_cpus_not_set_then_defaults_to_half_of_cpu_count(monkeypatch, tmp_path):
    """ADR 0006 Layer 2: 50% of host cores."""
    sub = tmp_path / "submission.py"; sub.write_text("class Solver: ...")
    reports = tmp_path / "reports"

    fake_run, captured = _make_fake_docker(reports)
    monkeypatch.setattr(subprocess, "run", fake_run)

    scorer = DockerCanonicalScorer(cpu_count_port=FixedCpuCount(24))
    scorer._score_path(sub, seeds=(1, 2), hard_wall_sec=10.0, reports_root=reports)

    cmd = captured["cmd"]
    assert "--cpus=12.0" in cmd, f'expected --cpus=12.0 (24/2); cmd: {cmd}'


@pytest.mark.no_fake
def test_when_default_image_then_v04_used():
    """The Dockerfile bumped to v0.4 in cycle 105 sub-A; adapter default must match."""
    assert _DEFAULT_IMAGE == "reward-bench-tier1:0.4", (
        f'default image must be v0.4; got {_DEFAULT_IMAGE}'
    )
