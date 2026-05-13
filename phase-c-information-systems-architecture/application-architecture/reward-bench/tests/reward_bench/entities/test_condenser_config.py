"""CondenserConfig tests. See tests-spec/reward_bench/entities/condenser_config/."""
import dataclasses

import pytest

from src.reward_bench.entities.condenser_config import CondenserConfig


def test_when_condenser_config_constructed_then_fields_preserved():
    # Arrange

    # Act
    c = CondenserConfig(
        trigger_tokens=40000,
        keep_recent=8,
        model_id='condenser-llama31-8b',
    )

    # Assert
    assert c.trigger_tokens == 40000
    assert c.keep_recent == 8
    assert c.model_id == 'condenser-llama31-8b'
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.trigger_tokens = 0  # type: ignore[misc]
