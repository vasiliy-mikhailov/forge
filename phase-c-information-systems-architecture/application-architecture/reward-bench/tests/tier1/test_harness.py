"""Tier 1 harness tests. See spec/tier1/harness.md."""
import sys
from pathlib import Path

# Make repo root importable so 'bench.tier1.harness' resolves.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bench.tier1.harness import load_submission


def test_when_reference_fsm_loaded_then_exposes_class_solver():
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    reference = repo / 'tasks/2048/baselines/reference_fsm.py'

    # Act
    Solver = load_submission(reference)

    # Assert
    assert Solver.__name__ == 'Solver'


def test_when_reference_fsm_solver_instantiated_then_returns_instance():
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    Solver = load_submission(repo / 'tasks/2048/baselines/reference_fsm.py')

    # Act
    instance = Solver()

    # Assert
    assert isinstance(instance, Solver)


def test_when_reference_fsm_move_called_on_starting_board_then_returns_one_of_wasd():
    # Arrange
    repo = Path(__file__).resolve().parents[2]
    Solver = load_submission(repo / 'tasks/2048/baselines/reference_fsm.py')
    solver = Solver()
    starting_board = [
        [2, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 2],
        [0, 0, 0, 0],
    ]

    # Act
    move = solver.move(starting_board)

    # Assert
    assert move in {'W', 'A', 'S', 'D'}
