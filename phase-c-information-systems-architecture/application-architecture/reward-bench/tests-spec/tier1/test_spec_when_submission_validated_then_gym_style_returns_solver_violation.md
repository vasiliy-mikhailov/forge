# `test_when_submission_validated_then_gym_style_returns_solver_violation`

Pins the gym-style failure mode: a submission that defines `def
solve(grid)` instead of `class Solver` yields at least one violation
mentioning `Solver`.

## Contract

- **Arrange**: `tmp_path/submission.py` containing only
  `def solve(grid): return 0`.
- **Act**: `load_submission(p)` then `validate_submission_protocol(mod)`.
- **Assert**: `len(violations) >= 1`; some violation string contains
  `'Solver'`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../tests/tier1/test_harness.py`](../../tests/tier1/test_harness.py)::`test_when_submission_validated_then_gym_style_returns_solver_violation`.

## Runtime scope

> **Runtime scope**: unit only.
