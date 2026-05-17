# `test_when_submission_validated_then_valid_solver_returns_empty_tuple`

Pins the happy-path of `validate_submission_protocol`: a submission
with `class Solver` and `move(board) -> 'W'` returns an empty
violations tuple.

## Contract

- **Arrange**: `tmp_path/submission.py` with a minimal valid Solver
  (no-arg `__init__`, `move(board)` returning `'W'`).
- **Act**: `load_submission(p)` then `validate_submission_protocol(mod)`.
- **Assert**: `violations == ()`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../tests/tier1/test_harness.py`](../../tests/tier1/test_harness.py)::`test_when_submission_validated_then_valid_solver_returns_empty_tuple`.

## Runtime scope

> **Runtime scope**: unit only.
