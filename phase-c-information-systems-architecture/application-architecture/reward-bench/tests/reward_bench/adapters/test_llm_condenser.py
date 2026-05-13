"""LlmCondenser tests. See tests-spec/reward_bench/adapters/llm_condenser/."""
from src.reward_bench.adapters.llm_condenser import LlmCondenser
from src.reward_bench.entities.condenser_config import CondenserConfig


def test_when_llm_condenser_compacts_then_summary_appended_to_system_message_and_older_turns_dropped():
    # Arrange
    messages = (
        {'role': 'system', 'content': 'YOU-ARE-AN-AGENT'},
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

    # Assert: ONE system message (no second one — chat-template invariant)
    assert len(result) == 1 + 2, f'expected 3 messages, got {len(result)}'
    assert result[0]['role'] == 'system'
    assert 'YOU-ARE-AN-AGENT' in result[0]['content']
    assert 'STUB-SUMMARY' in result[0]['content']
    # Keep-recent window preserved verbatim
    assert result[-2:] == messages[-2:]
    # summarise called with the 4 older turns
    assert len(calls) == 1
    assert len(calls[0]) == 4
