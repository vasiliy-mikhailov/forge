# `test_when_src_modules_walked_then_each_referenced_by_at_least_one_src_spec`

Architecture / fitness-function. Every non-trivial `src/*.py`
module (excluding `__init__.py` and `__pycache__/`) must be
referenced by at least one `src_spec_*.md` — either by its relative
path or its dotted module name.

Currently strict: `EXPECTED_MAX_ORPHAN_SRC_MODULES = 0`. No orphan
source modules exist; any new src/ file without a spec fails the
fast gate.

## Contract

- **Arrange**: discover all `src/**/*.py` files (skip `__init__.py`,
  `__pycache__/`). Concatenate all `src_spec_*.md` content.
- **Act**: orphans = modules whose relative-path string AND dotted
  module name both absent from concatenated spec text.
- **Assert**: `len(orphans) <= EXPECTED_MAX_ORPHAN_SRC_MODULES`.

## Model client injection point

- **Seam**: none — pure filesystem walk + string search.

Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_src_modules_walked_then_each_referenced_by_at_least_one_src_spec`.

## Runtime scope

> **Runtime scope**: unit only.
