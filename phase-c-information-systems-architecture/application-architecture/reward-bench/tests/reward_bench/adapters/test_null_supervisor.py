"""NullSupervisor + SupervisorPort runtime-checkable conformance tests.

See tests-spec/reward_bench/adapters/null_supervisor/."""
from src.ports.supervisor import SupervisorPort
from src.reward_bench.adapters.null_supervisor import NullSupervisor
from src.reward_bench.entities.supervisor_decision import SupervisorDecision


def test_when_null_supervisor_judges_then_returns_never_stop_decision():
    # Arrange
    sweep = (
        (1, 3000.0, 256, 1.0),
        (2, 3000.0, 256, 1.0),
        (3, 3000.0, 256, 1.0),
    )
    supervisor = NullSupervisor()

    # Act
    decision = supervisor.judge(sweep)

    # Assert
    assert isinstance(decision, SupervisorDecision)
    assert decision.plateau is False
    assert decision.stop_recommended is False
    assert isinstance(decision.reasoning, str)
    assert decision.reasoning  # non-empty
    assert isinstance(supervisor, SupervisorPort)
