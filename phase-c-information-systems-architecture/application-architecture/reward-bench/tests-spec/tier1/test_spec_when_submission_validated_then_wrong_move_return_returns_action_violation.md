# `test_when_submission_validated_then_wrong_move_return_returns_action_violation`

Pins the return-type violation: `move()` returning an `int` (not one
of `W`/`A`/`S`/`D`) yields a violation mentioning either the allowed
actions or `str`.

## Contract

- **Arrange**: `tmp_path/submission.py` with `class Solver` whose
  `move()` returns `0` instead of an action string.
- **Act**: `validate_submission_protocol(mod)`.
- **Assert**: at least one violation contains either `W`+`A` substrings
  OR the word `str` (case-insensitive).

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../tests/tier1/test_harness.py`](../../tests/tier1/test_harness.py)::`test_when_submission_validated_then_wrong_move_return_returns_action_violation`.

## Runtime scope

> **Runtime scope**: unit only.
