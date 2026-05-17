# `test_when_test_functions_walked_then_each_has_a_corresponding_test_spec`

Architecture / fitness-function. Walks every `test_when_X_then_Y`
function under `tests/` and asserts a `test_spec_when_X_then_Y.md`
exists somewhere under `tests-spec/`. Enforces "no code without a
spec" from the code-already-exists side.

Ratchet: `EXPECTED_MAX_ORPHAN_TESTS` decremented as each orphan is
spec'd or removed; when 0, defect class permanently extinct.

## Contract

- **Arrange**: discover all `test_when_*` function names in
  `tests/**/*.py`. Collect spec stems
  (`test_spec_when_X_then_Y.md` → `test_when_X_then_Y`).
- **Act**: orphans = test function names not present in the spec
  stem set.
- **Assert**: `len(orphans) <= EXPECTED_MAX_ORPHAN_TESTS`.

## Model client injection point

- **Seam**: none — pure filesystem walk.

Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_test_functions_walked_then_each_has_a_corresponding_test_spec`.

## Runtime scope

> **Runtime scope**: unit only.
