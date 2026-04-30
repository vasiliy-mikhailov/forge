# T-WP-01 — Wiki PM extracts rules from raw transcript per capability dimensions

## Scenario

**Given** a single raw Kurpatov lecture transcript
(`raw.json` under `kurpatov-wiki-raw/data/<course>/<module>/<stem>/`),
**when** the [Wiki PM agent](../wiki-pm.md) executes Steps S1–S2
of [`wiki-requirements-collection.md`](../../../phase-requirements-management/wiki-requirements-collection.md)
on that raw,
**then** it produces a corpus-observations file in which the
quoted observations (a) are verbatim sub-strings of the raw, (b)
are bucketed Substance / Form / Air, and (c) cover at least one
observation per quality dimension of the
[`Develop wiki product line`](../../capabilities/develop-wiki-product-line.md)
capability — so that the rules the agent will later emit in S7
have evidence aligned to the dimensions they will close.

This is the test the architect described as the first thing the
agent should be able to do: *"when wiki PM sees raw wiki it can
extract rules according to develop wiki product line capability."*

## Fixture

- **Persona.** [`../wiki-pm.md`](../wiki-pm.md)
- **Activation.** [`../../../phase-requirements-management/wiki-requirements-collection.md`](../../../phase-requirements-management/wiki-requirements-collection.md),
  Steps S1–S2 only (the rest of the process is exercised by other
  tests).
- **Capability dimensions to cover.** From the
  [Quality dimensions](../../capabilities/develop-wiki-product-line.md)
  table:
  1. Voice preservation
  2. Reading speed
  3. Dedup correctness
  4. Fact-check coverage
  5. Concept-graph quality
  6. Reproducibility
  7. Transcription accuracy
  8. Requirement traceability
- **Raw input.** Pick one of:
  - `kurpatov-wiki-raw/data/Психолог-консультант/000 Путеводитель по программе/000 Знакомство с программой «Психолог-консультант»/raw.json`
    (88-min spoken lecture, ~10K words — the dense one)
  - `…/002 Вводная лекция в программу/raw.json`
    (~3.4K words, written-style конспект — the sparse one)
- **Expected output location.**
  `forge/phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`
  (architect creates this folder if absent).

## Acceptance

A verifier passes if **all** of the following hold over the
agent's output:

1. **File exists** at the expected output location and is
   non-empty (`wc -l` ≥ 30).
2. **Three buckets present.** The file contains the headers
   `## Substance`, `## Form`, `## Air` (case-insensitive,
   levels-2 markdown).
3. **Verbatim quotes.** Every observation includes a quoted
   string (` `…` ` or block-quote `>`); for each such quote, that
   exact substring appears in the raw transcript text after
   trivial whitespace normalisation. (Verifier: load
   `raw.json["segments"][*]["text"]`, concatenate, normalise
   whitespace, search for each quote substring.)
4. **No invented quotes.** No quoted string in the output is
   absent from the raw — i.e. there is no quote the verifier
   cannot find.
5. **Coverage ≥ 6 dimensions.** Across the Form and Air buckets,
   the agent has emitted at least one observation labelled (in
   prose or in the entry's footer) as relevant to ≥ 6 of the 8
   capability quality dimensions enumerated in Fixture above.
   "Voice preservation" alone counts once — repeated
   observations under the same dimension don't multiply
   coverage.
6. **No empty bucket.** Each of Substance / Form / Air contains
   at least 3 observations.
7. **No persona violation.** The agent has NOT also written R-NN
   rows into `phase-requirements-management/catalog.md` (S7 is
   out of scope for this test; emitting catalog rows here means
   the agent ran past its instructions).
8. **No schema edit.** No file under
   `phase-c-information-systems-architecture/application-architecture/wiki-bench/`
   was modified by the agent (that is the developer-agent
   territory; Wiki PM escalates schema changes — see T-WP-03).

## Run

1. **Setup.** Architect ensures the output folder
   `phase-b-business-architecture/products/kurpatov-wiki/`
   exists. Cowork session is fresh.
2. **Activation.** Hand the session this prompt verbatim:
   *"Load `forge/phase-b-business-architecture/agents/wiki-pm.md`
   as your persona. Then load
   `forge/phase-requirements-management/wiki-requirements-collection.md`
   and execute Steps S1 and S2 ONLY against the raw transcript at
   `<path-to-raw.json>`. Output goes to
   `forge/phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`.
   Stop after S2 — do NOT proceed to S3+."*
3. **Wait** for output. Cap session at 30 minutes; if longer, the
   test's first failure is "agent could not complete S1-S2 in
   bounded time" and the persona / process step needs tightening.
4. **Verify mechanically.**
   - 4a. `test -s phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md` (Acceptance #1).
   - 4b. `grep -c '^## ' …/corpus-observations.md` and confirm
        the three required headers exist (#2).
   - 4c. Extract every backtick-quoted or `> `-prefixed line from
        the output file; for each, search for the substring in
        the raw transcript text. Report any miss (#3, #4).
   - 4d. Count observations per bucket (#6).
   - 4e. Parse coverage labels in observation footers; check
        against the 8 dimensions list (#5).
   - 4f. `git status --porcelain phase-c-…/wiki-bench/ \
        phase-requirements-management/catalog.md` — must be
        empty (#7, #8).
5. **Eye-read** if 4a-4f all pass. The test does not enforce
   readability mechanically; the architect spot-checks 5
   randomly chosen observations to confirm they are substantive,
   not whitespace-padded fillers.

## Status

`RED` — agent has not yet been run on the kurpatov-wiki corpus.
First run is gated on T-WP-02 and T-WP-03 also being drafted, so
all three persona facets are simultaneously under test from the
agent's first contact with the corpus.

## Coverage map

This test exercises:

- Persona Output line: *"Working evidence file
  (`products/<wiki>/corpus-observations.md`)"*.
- Persona Output line: *"verbatim quoted observations cited by
  R-NN rows. Provenance."*
- Capability quality dimensions: all 8 of them, indirectly
  (the test asserts the agent has *seen* observations
  attributable to each dimension, even if it has not yet
  authored R-NN rows that close them — that is T-WP-02's
  territory).
- Persona Decision-right: *"Which observations to bucket as
  Substance / Form / Air in S2."*
