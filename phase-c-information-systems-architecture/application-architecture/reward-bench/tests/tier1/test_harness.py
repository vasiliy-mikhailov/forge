import pytest
"""Tier 1 harness tests. See src-spec/tier1/ and tests-spec/tier1/."""
import inspect
import tempfile
from pathlib import Path

from src.tier1.harness import load_submission
from src.tier1.adapters.parser import extract_python


def _write_submission(skill_tier1_reply):
    source = extract_python(skill_tier1_reply)
    f = tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False)
    f.write(source)
    f.close()
    return Path(f.name)


def test_when_extracted_module_loaded_then_exposes_class_solver(skill_tier1_reply):
    # Arrange
    submission = _write_submission(skill_tier1_reply)

    # Act
    module = load_submission(submission)

    # Assert
    assert hasattr(module, 'Solver'), 'submission has no Solver attribute'
    assert inspect.isclass(module.Solver), 'Solver is not a class'


@pytest.mark.live
def test_when_solver_class_instantiated_then_exposes_callable_move(skill_tier1_reply):
    # Arrange
    submission = _write_submission(skill_tier1_reply)
    module = load_submission(submission)

    # Act
    instance = module.Solver()
    move = getattr(instance, 'move', None)

    # Assert
    assert isinstance(instance, module.Solver), 'Solver() did not return a Solver'
    assert callable(move), 'Solver instance has no callable move attribute'



def test_when_submission_validated_then_valid_solver_returns_empty_tuple(tmp_path):
    """Cycle 53: pin the canonical valid-submission shape."""
    from src.tier1.harness import load_submission, validate_submission_protocol
    p = tmp_path / 'submission.py'
    p.write_text(
        'class Solver:\n'
        '    def __init__(self):\n'
        '        pass\n'
        '    def move(self, board):\n'
        "        return 'W'\n"
    )
    mod = load_submission(p)
    violations = validate_submission_protocol(mod)
    assert violations == (), f'expected no violations; got {violations!r}'


def test_when_submission_validated_then_gym_style_returns_solver_violation(tmp_path):
    """Cycle 53: pin the Gym-style failure mode (what the model wrote)."""
    from src.tier1.harness import load_submission, validate_submission_protocol
    p = tmp_path / 'submission.py'
    p.write_text(
        'def solve(grid):\n'
        '    return 0\n'
    )
    mod = load_submission(p)
    violations = validate_submission_protocol(mod)
    assert len(violations) >= 1, 'expected at least one violation'
    assert any('Solver' in v for v in violations), (
        f'expected a Solver-class violation; got {violations!r}'
    )


def test_when_submission_validated_then_wrong_move_return_returns_action_violation(tmp_path):
    """Cycle 53: pin the return-shape violation."""
    from src.tier1.harness import load_submission, validate_submission_protocol
    p = tmp_path / 'submission.py'
    p.write_text(
        'class Solver:\n'
        '    def __init__(self):\n'
        '        pass\n'
        '    def move(self, board):\n'
        '        return 0\n'  # wrong: int instead of str
    )
    mod = load_submission(p)
    violations = validate_submission_protocol(mod)
    assert any('W' in v and 'A' in v for v in violations) or any(
        'str' in v.lower() for v in violations
    ), f'expected return-type violation; got {violations!r}'


def test_when_submission_validated_then_missing_move_returns_method_violation(tmp_path):
    """Cycle 53: pin the missing-method violation."""
    from src.tier1.harness import load_submission, validate_submission_protocol
    p = tmp_path / 'submission.py'
    p.write_text(
        'class Solver:\n'
        '    def __init__(self):\n'
        '        pass\n'
        '    def select_action(self, observation):\n'
        "        return 'W'\n"
    )
    mod = load_submission(p)
    violations = validate_submission_protocol(mod)
    assert any('move' in v for v in violations), (
        f'expected a move-method violation; got {violations!r}'
    )


def test_when_submission_source_lacks_transitions_import_then_violation(tmp_path):
    """Cycle 91 / SPEC.md Tier 1: validate_submission_protocol(module, source=...)
    grep-rejects submissions missing 'from transitions import'."""
    from src.tier1.harness import load_submission, validate_submission_protocol

    body = (
        'class Solver:\n'
        '    def __init__(self): pass\n'
        '    def move(self, board):\n'
        "        return 'W'\n"
    )
    sub = tmp_path / 'submission.py'
    sub.write_text(body)
    mod = load_submission(str(sub))

    violations = validate_submission_protocol(mod, source=body)

    assert violations, 'expected at least one violation; got empty'
    assert any('transitions' in v and 'import' in v for v in violations), (
        f"expected a violation mentioning 'transitions' and 'import'; got {violations}"
    )


def test_when_submission_source_imports_transitions_then_no_transitions_violation(tmp_path):
    """Negative-control for cycle 91: body with 'from transitions import Machine'
    yields no transitions-related violation."""
    from src.tier1.harness import load_submission, validate_submission_protocol

    body = (
        'from transitions import Machine\n'
        'class Solver:\n'
        '    def __init__(self): pass\n'
        '    def move(self, board):\n'
        "        return 'W'\n"
    )
    sub = tmp_path / 'submission.py'
    sub.write_text(body)
    mod = load_submission(str(sub))

    violations = validate_submission_protocol(mod, source=body)

    assert not any('transitions' in v for v in violations), (
        f'unexpected transitions violation; got {violations}'
    )
