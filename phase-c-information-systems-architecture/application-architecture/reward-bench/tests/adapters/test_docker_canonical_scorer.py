"""DockerCanonicalScorer tests."""
from __future__ import annotations


def test_when_docker_canonical_scorer_score_body_called_then_inner_score_receives_tempfile_with_body():
    """Pins §7.5 body-in API on production scorer. score_body marshals
    body string to a private tempfile and delegates internally; path
    never escapes the method."""
    # Arrange
    from pathlib import Path

    from src.tier1.adapters.docker_canonical_scorer import (
        DockerCanonicalScorer,
    )
    from src.tier1.entities.attempt_result import AttemptResult

    captured: dict = {}
    stub_result = AttemptResult(
        mean_score=0.0, median_score=0.0, std_score=0.0,
        max_max_tile=0, n_games=0, aggregate_walltime_sec=0.0,
        games=(), hard_wall_sec=0.0,
        stagnated_any=False, walltime_exceeded=False,
    )

    scorer = DockerCanonicalScorer()

    def stub_score(submission_path, seeds, *, hard_wall_sec=0.0,
                   reports_root=None):
        captured['submission_path'] = str(submission_path)
        captured['body_contents'] = Path(submission_path).read_text()
        return stub_result

    scorer.score = stub_score

    # Act
    result = scorer.score_body(body='class Solver: pass\n', seeds=(1,))

    # Assert
    assert result is stub_result
    assert captured['body_contents'] == 'class Solver: pass\n'
