# `test_when_src_spec_corpus_walked_then_no_cycle_archaeology_present`

Architecture / fitness-function test, parallel to the tests-spec
archaeology check. Walks every `src_spec_*.md` under `src-spec/` and
asserts no `cycle <n>` / `Cycle <n>` / `ADR <NNNN>` patterns in body
prose. Per the cats.md *Git is the history; specs describe the
current decision* rule.

## Contract

- **Arrange**: discover every file matching
  `src-spec/**/src_spec_*.md` under the repo root.
- **Act**: for each file, scan body lines for archaeology patterns.
- **Assert**: zero violations across the corpus.

## Model client injection point

- **Seam**: none — pure filesystem walk + regex.

Test code: [`../../tests/architecture/test_spec_shape.py`](../../tests/architecture/test_spec_shape.py)::`test_when_src_spec_corpus_walked_then_no_cycle_archaeology_present`.

## Runtime scope

> **Runtime scope**: unit only — corpus-wide structural test.
