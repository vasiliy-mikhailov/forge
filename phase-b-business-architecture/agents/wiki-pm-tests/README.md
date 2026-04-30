# Wiki PM agent — MD tests

The pass/fail spec for the [Wiki PM agent](../wiki-pm.md). Tests
follow the convention in
[`../README.md` § "MD tests for agents (TDD discipline)"](../README.md).

## Coverage targets

| Persona responsibility / quality dimension                                | Tests                                |
|---------------------------------------------------------------------------|--------------------------------------|
| Outputs: corpus-observations.md (S1-S2 evidence file)                     | T-WP-01                              |
| Outputs: R-NN rows in `phase-requirements-management/catalog.md`          | T-WP-01, T-WP-02                     |
| Outputs: per-wiki product-side artefacts (Reading modes, Goals, UCs, IA)  | (no test yet — coverage hole)        |
| Realises: Requirement traceability dimension of [`Develop wiki product line`](../../capabilities/develop-wiki-product-line.md) | T-WP-01, T-WP-02 |
| Decision rights: emits / supersedes R-NN rows                             | T-WP-02                              |
| Decision rights: chooses Substance / Form / Air bucketing                 | T-WP-01                              |
| Escalates: schema changes, prompt changes, source.md edits                | T-WP-03                              |
| Escalates: Phase A goals, trajectory model rules                          | (no test yet — coverage hole)        |

Coverage status: **L1** (1 test drafted; targeting L3 once the
three-test suite below all goes `GREEN`).

## Tests

| ID       | Title                                                            | Status |
|----------|------------------------------------------------------------------|--------|
| T-WP-01  | [Extract rules from raw transcript per capability dimensions](T-WP-01-extract-rules-from-raw.md) | RED |
| T-WP-02  | [No orphan R-NN rows — every row cites evidence and a quality dimension](T-WP-02-no-orphan-rules.md) | RED |
| T-WP-03  | [Agent escalates schema / prompt / source.md changes — does not edit them directly](T-WP-03-escalates-schema-changes.md) | RED |

All three tests are `RED` because the agent has not yet been run
for the first time. They become `GREEN` after the agent's first
run on the kurpatov-wiki corpus passes their predicates.

## Running

A runner is queued under task #23 (Step 3 — build measurement);
until then, tests are run by the architect by:

1. Loading the agent's persona + activation file in a Cowork
   session.
2. Handing the agent the fixture(s) listed in the test.
3. Reviewing the output against the test's Acceptance section
   (mechanical predicates first, eye-read for what mechanical
   can't reach).
4. Writing the result into the test file's Status line as a
   commit.

Once the runner exists, this step becomes `make wiki-pm-tests`.

## Adding new tests

When evidence shows a gap (the agent produces something that
violates a persona statement, or the catalog grows a new R-NN
that no test covers), draft a new test in this folder, append it
to the table above with `Status: RED`, and update the
coverage-targets table.
