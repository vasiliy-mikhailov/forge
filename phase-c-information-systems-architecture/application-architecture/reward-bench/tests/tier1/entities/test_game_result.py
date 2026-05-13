"""GameResult tests. See tests-spec/tier1/entities/game_result/."""
import dataclasses

import pytest

from src.tier1.entities.game_result import GameResult


_FINAL_STATES = (
    'won', 'lost', 'max_moves',
    'stagnated', 'walltime_exceeded',
    'solver_error', 'invalid_action',
)


def test_when_game_result_constructed_then_fields_preserved():
    # Arrange (real-system values: seed 1000 baseline FSM, ref FSM score)

    # Act
    g = GameResult(
        seed=1000, score=7211, max_tile=512, moves=614,
        final_state='lost', walltime_sec=0.182,
    )

    # Assert
    assert g.seed == 1000
    assert g.score == 7211
    assert g.max_tile == 512
    assert g.moves == 614
    assert g.final_state == 'lost'
    assert g.walltime_sec == 0.182
    with pytest.raises(dataclasses.FrozenInstanceError):
        g.score = 0  # type: ignore[misc]


@pytest.mark.parametrize('final_state', _FINAL_STATES)
def test_when_game_result_constructed_with_each_final_state_literal_then_accepted(final_state):
    # Arrange (trivial values; only final_state varies)

    # Act
    g = GameResult(seed=0, score=0, max_tile=2, moves=0,
                   final_state=final_state, walltime_sec=0.0)

    # Assert
    assert g.final_state == final_state
