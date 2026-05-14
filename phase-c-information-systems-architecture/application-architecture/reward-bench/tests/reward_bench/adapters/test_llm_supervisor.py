"""LlmSupervisor tests.

See tests-spec/reward_bench/adapters/llm_supervisor/."""
from src.reward_bench.adapters.llm_supervisor import LlmSupervisor
from src.reward_bench.entities.supervisor_decision import SupervisorDecision


def test_when_llm_supervisor_called_with_plateau_sweep_then_returns_stop_decision_from_reply():
    # Arrange — record prompt; reply with a model's "yes plateau" verdict.
    captured = {'prompt': None}
    def ask(prompt):
        captured['prompt'] = prompt
        return (
            '{"plateau": true, '
            '"reasoning": "score flat at 3000 for 5 turns", '
            '"stop_recommended": true}'
        )
    sweep = (
        (1, 3000.0, 256, 1.0),
        (2, 3000.0, 256, 1.0),
        (3, 3000.0, 256, 1.0),
    )

    # Act
    decision = LlmSupervisor(ask, 'qwen3.6-27b-awq').judge(sweep)

    # Assert — decision parsed from reply
    assert isinstance(decision, SupervisorDecision)
    assert decision.plateau is True
    assert decision.stop_recommended is True
    assert decision.reasoning == 'score flat at 3000 for 5 turns'

    # Assert — prompt actually carried the sweep data
    assert captured['prompt'] is not None
    assert '3000' in captured['prompt']
    assert 'plateau' in captured['prompt']


def test_when_llm_supervisor_reply_unparseable_then_returns_conservative_fallback():
    # Arrange — reply contains no JSON.
    def ask(prompt):
        return "I think this is plateau but I'm not sure"
    sweep = ((1, 3000.0, 256, 1.0),)

    # Act
    decision = LlmSupervisor(ask, 'qwen3.6-27b-awq').judge(sweep)

    # Assert — conservative fallback
    assert decision.plateau is False
    assert decision.stop_recommended is False
    assert decision.reasoning.startswith('supervisor parse-error:'), (
        f"reasoning was {decision.reasoning!r}"
    )


def test_when_llm_supervisor_ask_raises_then_returns_conservative_fallback():
    """no-silent-fix: ask() throwing must NOT propagate to the agent loop."""
    # Arrange
    def ask(prompt):
        raise ConnectionError('vLLM unreachable')
    sweep = ((1, 3000.0, 256, 1.0),)

    # Act
    decision = LlmSupervisor(ask, 'qwen3.6-27b-awq').judge(sweep)

    # Assert
    assert decision.plateau is False
    assert decision.stop_recommended is False
    assert decision.reasoning.startswith('supervisor parse-error:'), (
        f"reasoning was {decision.reasoning!r}"
    )


def test_when_llm_supervisor_reply_missing_keys_then_returns_conservative_fallback():
    """JSON parseable but schema-incomplete — same conservative path."""
    # Arrange — JSON without 'plateau' key.
    def ask(prompt):
        return '{"reasoning": "yes", "stop_recommended": true}'
    sweep = ((1, 3000.0, 256, 1.0),)

    # Act
    decision = LlmSupervisor(ask, 'qwen3.6-27b-awq').judge(sweep)

    # Assert
    assert decision.plateau is False
    assert decision.stop_recommended is False
    assert decision.reasoning.startswith('supervisor parse-error:')
