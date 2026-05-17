# `test_when_submission_validated_then_missing_move_returns_method_violation`

Pins the missing-method violation: a `Solver` class that defines
`select_action()` instead of `move()` yields a violation mentioning
`move`.

## Contract

- **Arrange**: `tmp_path/submission.py` with `class Solver` defining
  `select_action(self, observation)` (no `move`).
- **Act**: `validate_submission_protocol(mod)`.
- **Assert**: at least one violation contains `'move'`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../tests/tier1/test_harness.py`](../../tests/tier1/test_harness.py)::`test_when_submission_validated_then_missing_move_returns_method_violation`.

## Runtime scope

> **Runtime scope**: unit only.
