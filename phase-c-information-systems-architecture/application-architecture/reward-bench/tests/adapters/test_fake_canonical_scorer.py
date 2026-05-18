"""FakeCanonicalScorer tests."""
from __future__ import annotations


def test_when_fake_canonical_scorer_score_body_called_then_records_body_and_returns_scripted_result():
    """Pins §7.5 body-in API on the canonical scorer test double."""
    # Arrange
    from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
    from src.tier1.entities.attempt_result import AttemptResult

    expected = AttemptResult(
        mean_score=42.0, median_score=42.0, std_score=0.0,
        max_max_tile=128, n_games=3, aggregate_walltime_sec=5.0,
        games=(), hard_wall_sec=0.0,
        stagnated_any=False, walltime_exceeded=False,
    )
    fake = FakeCanonicalScorer(script=(expected,))

    # Act
    result = fake.score_body(body='class Solver: pass\n', seeds=(1, 2, 3))

    # Assert
    assert result is expected
    assert fake.calls[0]['body'] == 'class Solver: pass\n'
    assert fake.calls[0]['seeds'] == (1, 2, 3)
