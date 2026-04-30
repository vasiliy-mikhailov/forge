# T-WP-02 — No orphan R-NN rows: every row cites evidence and a quality dimension

## Scenario

**Given** the corpus-observations file produced by T-WP-01
(passing) AND the [Wiki PM agent](../wiki-pm.md) running Step S7
of [`wiki-requirements-collection.md`](../../../phase-requirements-management/wiki-requirements-collection.md)
on it,
**when** the agent emits R-NN rows into
[`phase-requirements-management/catalog.md`](../../../phase-requirements-management/catalog.md),
**then** every newly-emitted row carries (a) a citation back to ≥ 1
quoted observation in `corpus-observations.md` and (b) a Quality-dim
column whose value matches one of the eight quality dimensions of
the [`Develop wiki product line`](../../capabilities/develop-wiki-product-line.md)
capability — so that no row in the catalog can survive review
without provenance and a target dimension.

This test makes the persona's "Maintain provenance" responsibility
mechanically falsifiable.

## Fixture

- **Persona.** [`../wiki-pm.md`](../wiki-pm.md)
- **Activation.** [`../../../phase-requirements-management/wiki-requirements-collection.md`](../../../phase-requirements-management/wiki-requirements-collection.md),
  Step S7.
- **Required predecessor.** T-WP-01 must be `GREEN` for the same
  raw input — the corpus-observations file is the input here.
- **Quality-dim allow-list** (must match exactly one of):
  Voice preservation · Reading speed · Dedup correctness ·
  Fact-check coverage · Concept-graph quality · Reproducibility ·
  Transcription accuracy · Requirement traceability.
- **R-NN ID convention.** `R-B-<wiki>-<slug>` (per
  [`../../../phase-requirements-management/process.md`](../../../phase-requirements-management/process.md)
  ID convention plus per-wiki disambiguation).

## Acceptance

For every row added to `catalog.md` by the agent during this S7
run, all of the following hold:

1. **ID format.** Matches `^R-B-[a-z0-9-]+$` (Phase B prefix; lower
   slug). The slug uniquely identifies the row across the catalog
   (no duplicate ID).
2. **Provenance.** The row's "Source" cell contains a reference
   that resolves to a quoted observation in
   `products/kurpatov-wiki/corpus-observations.md`. The citation
   may be a section header, an observation index (e.g.
   `corpus-observations.md#obs-12`), or an inline quote that
   verifier substring-matches against the observations file.
3. **Quality dimension.** The "Quality dim" cell starts with a
   string that exactly matches one entry from the allow-list
   above (case- and whitespace-insensitive on the prefix). Free-
   text trailing description is allowed after the dimension
   name.
4. **Level 1 / Level 2 gap.** Both "Level 1 (today)" and "Level 2
   (next)" cells are non-empty. The Level-2 cell describes a
   testable property — verifier (or LLM-as-judge) confirms it
   could be implemented as a function over `(input, output) →
   pass | fail`.
5. **Status default.** The row's "Status" cell is `OPEN`. (The
   agent does not close rows.)
6. **No row collapses two dimensions.** Each row has exactly one
   Quality-dim entry. A row whose Level-2 cell asserts properties
   spanning two or more allow-list dimensions fails — the agent
   should have split it into two rows.
7. **Catalog still parses.** After the agent's edits,
   `phase-requirements-management/catalog.md` round-trips a
   markdown-table parser without error (no broken pipes, no
   misaligned columns).

## Run

1. **Pre-flight.** Confirm T-WP-01 status is `GREEN` for the
   chosen raw. If not, abort: this test depends on T-WP-01.
2. **Activation prompt** (verbatim to the agent):
   *"Continue from your S2 output at
   `forge/phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`.
   Skip S3-S6 for this run. Execute S7 only: emit R-NN rows into
   `forge/phase-requirements-management/catalog.md` for the
   observations you have. Do NOT modify any other file."*
3. **Snapshot.** Before the agent edits, snapshot
   `catalog.md` (e.g. `git stash` clean state). After the agent
   stops, diff to extract only the rows it added.
4. **Verify mechanically.** Iterate the diff:
   - 4a. ID matches regex (#1) and is unique in the file.
   - 4b. Provenance citation resolves: extract any inline quote
        and substring-match against `corpus-observations.md`;
        OR any `#anchor` reference exists.
   - 4c. Quality-dim prefix is on the allow-list (#3).
   - 4d. Both Level-1 and Level-2 cells non-empty (#4, partial).
   - 4e. Status cell == `OPEN` (#5).
   - 4f. Markdown-table parser round-trip (#7).
5. **LLM-as-judge** for #4 (testability) and #6 (single
   dimension): a *different* persona (e.g. a stub "skeptic"
   agent loaded only with the allow-list and the row text)
   answers yes/no on each row.
6. **Eye-read** sanity check: the architect reads 3 randomly
   chosen new rows and confirms they're not paraphrases of
   existing rows in the catalog.

## Status

`RED` — depends on T-WP-01.

## Coverage map

This test exercises:

- Persona Responsibility: *"Maintain provenance. Every requirement
  traces to either a raw-corpus observation or a stakeholder
  goal."*
- Persona Responsibility: *"Enforce acceptance-criterion rigour.
  Every requirement has a testable acceptance criterion."*
- Persona Output line: *"New / superseded `R-NN` rows in
  `phase-requirements-management/catalog.md`."*
- Persona Decision-right: *"emit / supersede R-NN rows."*
- Capability quality dimension: *Requirement traceability* — the
  binding dimension this test enforces directly.
- Capability quality dimensions: indirectly all eight, via #3
  (the allow-list ensures the agent's vocabulary stays aligned
  to the capability).
