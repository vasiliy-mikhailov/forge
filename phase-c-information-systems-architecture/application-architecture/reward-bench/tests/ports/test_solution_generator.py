"""SolutionGenerator Port tests."""
from __future__ import annotations


def test_when_solution_generator_port_inspected_then_generate_takes_snapshot():
    """Pins §2 SolutionGenerator: generate(self, snapshot) -> str.
    Pure function from a fresh ContextSnapshot to a SolverBody string."""
    # Arrange
    import inspect

    from src.ports.solution_generator import SolutionGenerator

    # Act
    params = list(inspect.signature(SolutionGenerator.generate).parameters)

    # Assert
    assert params == ['self', 'snapshot']
