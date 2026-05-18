"""InProcessCanonicalScorer tests."""
from __future__ import annotations


def test_when_in_process_canonical_scorer_score_body_called_then_score_submission_receives_solver_class(monkeypatch):
    """Pins §7.5 body-in API on in-process scorer. Body string is
    compiled in memory; the extracted Solver class is passed to
    score_submission without any path crossing the call."""
    # Arrange
    from src.adapters.in_process_canonical_scorer import (
        InProcessCanonicalScorer,
    )
    from src.tier1.entities.attempt_result import AttemptResult

    BODY = (
        "class Solver:\n"
        "    def move(self, board): return 'W'\n"
    )

    captured: dict = {}

    def stub_score_submission(solver_cls, seeds, env, *, hard_wall_sec=0.0):
        captured['solver_name'] = solver_cls.__name__
        return AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=0, n_games=0, aggregate_walltime_sec=0.0,
            games=(), hard_wall_sec=hard_wall_sec,
            stagnated_any=False, walltime_exceeded=False,
        )

    monkeypatch.setattr(
        'src.tier1.use_cases.score_submission.score_submission',
        stub_score_submission,
    )

    scorer = InProcessCanonicalScorer(env=object())

    # Act
    scorer.score_body(body=BODY, seeds=(1,))

    # Assert
    assert captured['solver_name'] == 'Solver'
