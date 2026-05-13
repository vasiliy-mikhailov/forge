"""CondenserPort tests. See tests-spec/reward_bench/use_cases/condenser_port/."""
from src.reward_bench.entities.condenser_config import CondenserConfig
from src.reward_bench.use_cases.condenser_port import CondenserPort, NullCondenser


def test_when_null_condenser_used_then_messages_pass_through_unchanged():
    # Arrange
    messages = (
        {'role': 'system', 'content': 'you are an agent'},
        {'role': 'user', 'content': 'start'},
        {'role': 'assistant', 'content': 'ok'},
    )
    config = CondenserConfig(
        trigger_tokens=40000, keep_recent=8,
        model_id='condenser-llama31-8b',
    )

    # Act
    condenser = NullCondenser()
    result = condenser.condense(messages, config)

    # Assert
    assert isinstance(condenser, CondenserPort)
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert result == messages
