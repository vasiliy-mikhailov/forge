# `test_when_test_spec_links_followed_then_referenced_test_function_exists`

Architecture / fitness-function test. Each `test_spec_*.md` ends
with a `Test code:` link pointing at a `.py` file and a test
function name. This test verifies the chain still resolves: the
file exists AND the function is defined in it.

Catches:
- Broken links (file renamed/moved, link not updated).
- Orphan specs (test deleted but spec kept).
- Drift between spec name and function name.

## Contract

- **Arrange**: discover every `tests-spec/**/test_spec_*.md` outside
  the `architecture/` meta-test dir.
- **Act**: for each, regex-extract the relative path and function
  name from the `Test code: [`<path>`](<path>)::`<name>`` line.
  Resolve the path against the spec's directory; check existence;
  grep the file for `def <name>(`.
- **Assert**: zero violations.

## Model client injection point

- **Seam**: none — pure filesystem walk + regex.

Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_test_spec_links_followed_then_referenced_test_function_exists`.

## Runtime scope

> **Runtime scope**: unit only — corpus-wide structural test.
