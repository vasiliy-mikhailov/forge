# `test_when_test_spec_corpus_walked_then_placeholder_count_at_or_below_known_max`

Architecture / fitness-function test. A **ratchet** that bounds the
count of test_specs still containing `(see test body ...)` placeholder
text. The cap is a module-level constant `EXPECTED_MAX_PLACEHOLDERS`
in the test file. The current baseline matches today's actual count;
every subsequent cycle that rewrites a stub also decrements the cap.

Why a ratchet rather than a hard `== 0`: per the operator preference
of "one spec at a time, fully CATS", the corpus cannot be brought to
zero placeholders in a single cycle. The ratchet pattern:
- Gates against **regression** — any newly-added placeholder fails
  the test.
- Tracks **progress** — the cap monotonically decreases.
- Forces **completion** — when `EXPECTED_MAX_PLACEHOLDERS == 0`, the
  test becomes a strict equality and the placeholder class of defect
  is permanently extinct.

## Contract

- **Arrange**: discover every file matching
  `tests-spec/**/test_spec_*.md` under the repo root. Compile the
  regex `\(see test body[^)]*\)`.
- **Act**: for each file, search its text for the pattern. Collect
  the relative paths of files where at least one match exists.
- **Assert**: `len(violations) <= EXPECTED_MAX_PLACEHOLDERS`. On
  failure, the message lists offending paths (truncated) so the
  operator can see exactly what regressed.

## Model client injection point

- **Seam**: none — pure filesystem walk + regex.
- **Mode**: n/a.
- **Marker**: none.

Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_test_spec_corpus_walked_then_placeholder_count_at_or_below_known_max`.

## Runtime scope

> **Runtime scope**: unit only — corpus-wide structural test; no I/O
> beyond the spec-files filesystem walk.
