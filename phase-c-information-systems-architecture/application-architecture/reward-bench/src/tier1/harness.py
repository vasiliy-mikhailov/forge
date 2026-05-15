"""Tier 1 harness. See src-spec/tier1/src_spec_when_extracted_module_*.md.

Also exposes `validate_submission_protocol` (cycle 53) for the
tier-1 submission contract from tasks/2048/SKILL_tier1.md."""
import importlib.util
import inspect


_VALID_ACTIONS = ('W', 'A', 'S', 'D')


def load_submission(path):
    spec = importlib.util.spec_from_file_location('submission', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_submission_protocol(module, source: str | None = None):
    """Return a tuple of human-readable violation strings.

    Empty tuple = the module satisfies the SKILL_tier1.md contract:
    `class Solver` with a `move(self, board) -> 'W'|'A'|'S'|'D'`
    method that can be instantiated with no args.

    Cycle 53: pinned by tests-spec/tier1/harness/
    test_spec_when_submission_validated_then_returns_violations_*.md.
    """
    violations = []

    Solver = getattr(module, 'Solver', None)
    if Solver is None:
        violations.append(
            "submission does not define a `Solver` class (required by SKILL_tier1.md)"
        )
        return tuple(violations)
    if not inspect.isclass(Solver):
        violations.append(
            "`Solver` exists but is not a class"
        )
        return tuple(violations)

    move = getattr(Solver, 'move', None)
    if move is None:
        violations.append(
            "Solver class has no `move` method "
            "(required signature: move(self, board) -> 'W'|'A'|'S'|'D')"
        )
        return tuple(violations)
    if not callable(move):
        violations.append("`Solver.move` is not callable")
        return tuple(violations)

    # Try to instantiate and call.
    try:
        instance = Solver()
    except Exception as e:
        violations.append(
            f"Solver() raised at construction: {type(e).__name__}: {e}"
        )
        return tuple(violations)

    test_board = [[0] * 4 for _ in range(4)]
    try:
        result = instance.move(test_board)
    except Exception as e:
        violations.append(
            f"Solver().move(empty_board) raised: {type(e).__name__}: {e}"
        )
        return tuple(violations)

    if not isinstance(result, str):
        violations.append(
            f"Solver().move() must return a str; got {type(result).__name__} "
            f"(expected one of W/A/S/D)"
        )
        return tuple(violations)
    if result not in _VALID_ACTIONS:
        violations.append(
            f"Solver().move() returned {result!r}; expected one of "
            f"W/A/S/D (per SKILL_tier1.md action mapping)"
        )
        return tuple(violations)

    # Cycle 91 / SPEC.md §Tier 1: soft-grep for `from transitions import`.
    # Only when caller passes the body source; back-compat for older
    # callers that don't have / don't pass the source.
    if source is not None and 'from transitions import' not in source:
        violations.append(
            "submission does not `from transitions import ...` (SPEC.md "
            "§Tier 1 requires the Solver class to use the `transitions` "
            "library to declare states + transitions — soft-grep enforced)"
        )
        return tuple(violations)

    return ()
