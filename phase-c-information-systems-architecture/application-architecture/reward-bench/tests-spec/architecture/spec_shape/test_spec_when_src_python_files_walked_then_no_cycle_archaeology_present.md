# `test_when_src_python_files_walked_then_no_cycle_archaeology_present`

Architecture / fitness-function. Walks every `src/**/*.py` and
asserts no `cycle <n>` / `Cycle <n>` / `ADR <NNNN>` patterns. Per
cats.md "Git is the history" — code describes the current decision
only.

Strict: `EXPECTED_MAX_SRC_PY_ARCHAEOLOGY = 0`. Pinned because cycle
134 already cleaned src/ to zero; this gate prevents regression.

## Contract

- **Arrange**: discover all `src/**/*.py` (skip `__pycache__/`).
- **Act**: scan each line for archaeology patterns.
- **Assert**: `len(violations) <= EXPECTED_MAX_SRC_PY_ARCHAEOLOGY`.

## Model client injection point

- **Seam**: none.

Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_src_python_files_walked_then_no_cycle_archaeology_present`.

## Runtime scope

> **Runtime scope**: unit only.
