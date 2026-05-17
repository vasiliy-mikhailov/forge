# `test_when_submission_source_imports_transitions_then_no_transitions_violation`

Negative-control for the transitions-import soft-grep: a body that
DOES `from transitions import Machine` must not emit a
transitions-related violation when `source=` is passed.

## Contract

- **Arrange**: `body` string with `from transitions import Machine` +
  valid `class Solver` returning `'W'`. Write to
  `tmp_path/submission.py`.
- **Act**: `validate_submission_protocol(mod, source=body)`.
- **Assert**: no violation string contains `'transitions'`.

## Model client injection point

- **Seam**: filesystem (tmp_path).
- **Mode**: fake.

Test code: [`../../tests/tier1/test_harness.py`](../../tests/tier1/test_harness.py)::`test_when_submission_source_imports_transitions_then_no_transitions_violation`.

## Runtime scope

> **Runtime scope**: unit only.
