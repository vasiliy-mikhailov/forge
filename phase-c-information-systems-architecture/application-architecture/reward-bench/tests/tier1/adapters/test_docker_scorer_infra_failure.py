"""Cycle 121: DockerCanonicalScorer raises on infrastructure failure.

See tests-spec/tier1/adapters/test_spec_when_score_invoked_with_missing_image_then_raises_runtime_error.md.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src.tier1.adapters.docker_canonical_scorer import DockerCanonicalScorer


_MISSING_IMAGE_STDERR = (
    "Unable to find image 'reward-bench-tier1:9.9' locally\n"
    "docker: Error response from daemon: pull access denied for "
    "reward-bench-tier1, repository does not exist or may require 'docker login': "
    "denied: requested access to the resource is denied.\n"
)


@pytest.mark.no_fake
def test_when_score_invoked_with_missing_image_then_raises_runtime_error(
    monkeypatch, tmp_path,
):
    # Arrange — fake subprocess returns image-missing error.
    sub_path = tmp_path / "submission.py"
    sub_path.write_text("class Solver:\n    def move(self, b): return 'W'\n")

    fake_proc = subprocess.CompletedProcess(
        args=["docker"], returncode=125, stdout="", stderr=_MISSING_IMAGE_STDERR,
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake_proc)

    scorer = DockerCanonicalScorer(
        image="reward-bench-tier1:9.9",
        cpus=2.0,
        env_path=None,
    )

    # Act + Assert
    with pytest.raises(RuntimeError) as exc_info:
        scorer.score(sub_path, seeds=(1, 2, 3),
                     hard_wall_sec=5.0,
                     reports_root=tmp_path / "reports")

    # The raised error must include the stderr content for diagnosis.
    assert "Unable to find image" in str(exc_info.value), (
        f"RuntimeError must echo the stderr image-missing detail; "
        f"got: {exc_info.value!r}"
    )


@pytest.mark.no_fake
def test_when_score_invoked_with_runtime_failure_then_sentinels_per_seed(
    monkeypatch, tmp_path,
):
    """Companion: container started + crashed mid-scoring (no
    infra-failure stderr) still sentinels as walltime_exceeded.

    Pre-existing behaviour preserved — pinning so the cycle-121 fix
    doesn't overcorrect and start raising on legitimate
    runner crashes."""
    sub_path = tmp_path / "submission.py"
    sub_path.write_text("class Solver:\n    def move(self, b): return 'W'\n")

    fake_proc = subprocess.CompletedProcess(
        args=["docker"], returncode=1,
        stdout="", stderr="Traceback... TypeError: solver crashed",
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake_proc)

    scorer = DockerCanonicalScorer(
        image="reward-bench-tier1:0.4",
        cpus=2.0,
        env_path=None,
    )

    # Act — should NOT raise; should produce walltime_exceeded sentinels.
    result = scorer.score(sub_path, seeds=(1, 2, 3),
                          hard_wall_sec=5.0,
                          reports_root=tmp_path / "reports")

    # Assert — 3 walltime_exceeded games, no raise.
    assert result.n_games == 3
    assert all(g.final_state == "walltime_exceeded" for g in result.games)
