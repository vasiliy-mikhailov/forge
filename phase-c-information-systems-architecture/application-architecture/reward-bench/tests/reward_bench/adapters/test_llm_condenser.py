"""LlmCondenser tests. See tests-spec/reward_bench/adapters/llm_condenser/."""
from src.reward_bench.adapters.llm_condenser import LlmCondenser
from src.reward_bench.entities.condenser_config import CondenserConfig


def test_when_llm_condenser_called_with_history_longer_than_keep_recent_then_older_turns_replaced_by_summary():
    # Arrange
    messages = (
        {'role': 'system', 'content': 'sys'},
        {'role': 'user', 'content': 'first'},
        {'role': 'assistant', 'content': 'reply1'},
        {'role': 'user', 'content': 'second'},
        {'role': 'assistant', 'content': 'reply2'},
        {'role': 'user', 'content': 'third'},
        {'role': 'assistant', 'content': 'reply3'},
    )
    config = CondenserConfig(
        trigger_tokens=0, keep_recent=2,
        model_id='qwen3.6-27b-awq',
    )
    calls = []
    def stub_summarise(older_turns):
        calls.append(older_turns)
        return f'STUB-SUMMARY of N={len(older_turns)} turns'

    # Act
    condenser = LlmCondenser(summarise=stub_summarise, model_id='qwen3.6-27b-awq')
    result = condenser.condense(messages, config)

    # Assert
    assert len(result) == 1 + 1 + 2, f'expected 4 messages, got {len(result)}'
    assert result[0] == messages[0]  # system preserved
    assert result[1]['role'] == 'system'
    assert 'STUB-SUMMARY' in result[1]['content']
    assert result[-2:] == messages[-2:]  # keep_recent window preserved
    assert len(calls) == 1
    assert len(calls[0]) == 4  # the 4 older turns
