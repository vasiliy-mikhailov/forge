# `test_when_test_spec_corpus_walked_then_no_cycle_archaeology_present`
Architecture / fitness-function test. Walks every `test_spec_*.md`
under `tests-spec/` and asserts none contains cycle archaeology
(`cycle <n>`, `Cycle <n>`, `cycles <a>/<b>`) or bare ADR references
(`ADR <n>`).
Per the cats.md *Git is the history; specs describe the current
decision* rule, the spec corpus describes the current decision only.
Historical cycle stamps and ADR numbers (now consolidated into
`SOLUTION-ARCHITECTURE.md`) belong in `git log`, not in spec bodies.
This is a **corpus-wide fitness function**: it cannot be silently
violated by adding a new spec, and it cannot quietly regress as old
specs accumulate stale references.
## Contract
- **Arrange**: discover every file matching
 `tests-spec/**/test_spec_*.md` under the repo root.
- **Act**: for each file, scan its text for patterns:
 `\bcycle\s+\d+`, `\bCycle\s+\d+`, `\bADR\s+\d{2,4}\b`.
- **Assert**: zero violations across the corpus. On failure, the test
 reports the full list of `(path, line_no, snippet)` triples so the
 operator can fix each.
## Model client injection point
- **Seam**: none — pure filesystem walk + regex.
- **Mode**: n/a.
- **Marker**: none (runs in the default fast gate).
Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_test_spec_corpus_walked_then_no_cycle_archaeology_present`.
## Runtime scope
> **Runtime scope**: unit only — corpus-wide structural test, no I/O
> beyond the spec-files filesystem walk. Scale-invariant: same
> behaviour at any spec count.
