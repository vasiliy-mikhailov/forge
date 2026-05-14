"""SupervisorDecision tests.

See tests-spec/reward_bench/entities/supervisor_decision/."""
from dataclasses import FrozenInstanceError

import pytest

from src.reward_bench.entities.supervisor_decision import SupervisorDecision


def test_when_supervisor_decision_constructed_then_fields_are_frozen_and_typed():
    # Arrange
    decision = SupervisorDecision(
        plateau=True,
        stop_recommended=False,
        reasoning='still exploring',
    )

    # Assert — fields
    assert decision.plateau is True
    assert decision.stop_recommended is False
    assert decision.reasoning == 'still exploring'

    # Assert — frozen
    with pytest.raises(FrozenInstanceError):
        decision.plateau = False  # type: ignore[misc]

    # Assert — annotations
    ann = SupervisorDecision.__annotations__
    assert ann['plateau'] is bool
    assert ann['stop_recommended'] is bool
    assert ann['reasoning'] is str
