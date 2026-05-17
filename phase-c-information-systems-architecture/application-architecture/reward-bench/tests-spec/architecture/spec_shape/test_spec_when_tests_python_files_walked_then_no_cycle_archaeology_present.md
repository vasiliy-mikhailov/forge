# `test_when_tests_python_files_walked_then_no_cycle_archaeology_present`

Architecture / fitness-function. Walks every `tests/**/*.py` and
asserts no `cycle <n>` / `Cycle <n>` / `ADR <NNNN>` patterns.

Ratchet: `EXPECTED_MAX_TESTS_PY_ARCHAEOLOGY = 29` (current baseline).
Naive regex-based strip is risky for test files (test fixtures
often contain triple-quoted Python strings that look like
docstrings); AST-based cleanup is future work. Each future cycle
decrements the ratchet.

## Contract

- **Arrange**: discover all `tests/**/*.py` (skip `__pycache__/`).
- **Act**: scan each line for archaeology patterns.
- **Assert**: `len(violations) <= EXPECTED_MAX_TESTS_PY_ARCHAEOLOGY`.

## Model client injection point

- **Seam**: none.

Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_tests_python_files_walked_then_no_cycle_archaeology_present`.

## Runtime scope

> **Runtime scope**: unit only.
