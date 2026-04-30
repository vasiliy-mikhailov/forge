# Wiki requirements collection

A wiki product (Phase B [products/](../phase-b-business-architecture/products/))
is harder to write requirements for than a service or a lab. The
input is a corpus the architect did not author, the output's value
depends on a reader who is not the architect, and the failure
modes ("the artifact passes structure but isn't usable") are
exactly the ones that don't surface in routine grading. This file
is the wiki-specific extension of [`process.md`](process.md) — the
*how to discover and emit* part for one new wiki, before the
general lifecycle takes over.

In TOGAF terms this is the Architecture Requirements specification
activity scoped to **wiki product lines** (Phase B
[`products/wiki-product-line.md`](../phase-b-business-architecture/products/wiki-product-line.md)
row "Wiki requirements collection"). The activity runs once when a
new wiki is opened (Kurpatov, Tarasov, future authors) and is
re-walked when material new evidence appears (a new module, a new
audience segment, a quality regression that no existing R-NN
explains).

This activity is performed by the
[Wiki PM role](../phase-b-business-architecture/roles/wiki-pm.md).
The role is filled today by a Claude session loaded with this
file as its working method; it is a separate org-unit from the
architect (who designs the structure) and from the labs (which
run the operational pipeline). See
[`../phase-b-business-architecture/org-units.md`](../phase-b-business-architecture/org-units.md)
for the split.

## When to walk the activity

Triggers (any one):

- A new wiki product is opening (e.g. Tarasov, future authors).
- A quality regression on an existing wiki traces to "no
  requirement covered this" — the catalog needs new R-NN rows.
- A new module of source material is added and it carries
  patterns the existing R-NN catalog doesn't account for.
- An implementation change cannot be made cleanly because the
  requirement it would serve is not in the catalog.

## Inputs

- **Raw source corpus** of the wiki — at least 5 representative
  raws spanning format, length, content-area variation. Read for
  *substance* (what the wiki must convey) and *form* (voice,
  structure, recurring patterns — drives anti-pattern
  identification).
- **Stakeholder evidence** — direct architect knowledge plus any
  external readers' input. Today the architect is identical to
  the reader (per
  [`../phase-a-architecture-vision/stakeholders.md`](../phase-a-architecture-vision/stakeholders.md)
  — End users are TBD); evidence comes from the architect's own
  reading-mode imagination of future readers.
- **Existing artifacts of the wiki** — current schema (frontmatter,
  section structure), current prompts, current grader. These
  surface implicit requirements that haven't been written down.
- **Existing decision records** — relevant ADRs that constrain
  what this wiki can or cannot be (e.g.
  [`../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/`](../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/)).

## Steps

Each step lists what it consumes, what it produces, and exit
criterion. Steps are not strictly sequential — early steps are
revisited as later ones surface evidence. The output of every
step is captured in the wiki's [products/](../phase-b-business-architecture/products/)
file (extend the existing per-product .md), with corpus
observations cited inline.

### S1 — Sample and pre-read corpus

**Input.** Raw corpus.
**Activity.** Pick ≥ 5 representative raws spanning format, length,
content-area variation. Read each once with no rule in mind —
absorb voice, density, structure variation. No notes yet.
**Output.** A list of sampled raws and brief structural notes per
sample, in the product file's "Corpus sample" section.
**Exit criterion.** Can answer: "what are the major formats this
wiki must handle, and which raws represent them?"

### S2 — Inventory observations

**Input.** S1 output + the raws.
**Activity.** For each raw, write quoted observations into three
buckets:
- **Substance** — actual content the source conveys.
- **Form** — recurring patterns of voice, structure, transitions.
- **Air** — material that, when removed, doesn't change the
  substance.
Keep quotes verbatim with file:line refs.
**Output.** Working evidence file (e.g.
`phase-b-business-architecture/products/<wiki>/corpus-observations.md`
or appended to the product file). May not survive into the final
deliverables — its content is the *evidence* later steps cite.
**Exit criterion.** Each sampled raw has ≥ 5 quoted observations
across the three buckets.

### S3 — Identify stakeholder reading modes

**Input.** S2 substance bucket + architect knowledge of intended
readers.
**Activity.** For each substance observation, ask: *who would read
this, in what mode, for what task?* Aggregate recurring reader
profiles into reading-mode segments. Confirm each segment
corresponds to a real intended reader (not artifact of corpus
alone).
**Output.** Extension to product file's "Reading modes" section.
Each entry: name, goals, reading mode (look-up / sequential
study / cross-reference / skim), information needs, anti-goals,
evidence pointers.
**Exit criterion.** Every reading-mode segment has ≥ 2 evidence
pointers. Anti-goals not blank.

### S4 — Decompose into product-level goals

**Input.** Reading modes from S3.
**Activity.** Each reader goal becomes a wiki-product-level goal
specific to *the wiki* (e.g. "a student preparing for an exam can
find the definition of a concept in under 10 seconds and verify
which lecture introduced it"), not the upstream organisational
goal. Each goal is rolled up to a Phase A goal (TTS, PTS, EB,
Architect-velocity) per
[`../phase-a-architecture-vision/goals.md`](../phase-a-architecture-vision/goals.md).
**Output.** Extension to product file's "Goals" section. Each entry:
goal, reading-mode refs, Phase A goal it rolls up to, success
criterion, anti-pattern.
**Exit criterion.** Every goal cites ≥ 1 reading-mode segment AND
rolls up to ≥ 1 Phase A goal. Every goal has an anti-pattern.

### S5 — Walk concrete reader scenarios

**Input.** Reading modes + goals.
**Activity.** For each (segment, goal) pair, walk literal steps the
reader takes. Each step lists the information they need at that
step. Surfaces use cases.
**Output.** Extension to product file's "Use cases" section. Each
entry: name, actor (reading-mode ref), trigger, steps (action +
information consumed), success outcome, failure modes.
**Exit criterion.** Every product goal is reachable from ≥ 1 use
case. Every use case cites ≥ 1 reading-mode segment.

### S6 — Reconcile against information architecture

**Input.** Use cases + existing wiki schema (entities + sections +
frontmatter fields).
**Activity.** Codify the wiki's entity model: what entities exist,
what attributes each carries, what relations connect them, what
existence rules apply. Where use cases need a new entity or
attribute, propose the addition; where existing schema has
attributes no use case needs, mark for review.
**Output.** Extension to product file's "Information architecture"
section, mirroring the wiki's actual schema. Each attribute
references the use case(s) that depend on it OR is justified as
structural metadata.
**Exit criterion.** Every attribute references ≥ 1 use case OR is
explicitly justified as provenance/structural.

### S7 — Emit requirements into the catalog

**Input.** All prior outputs + S2 evidence file.
**Activity.** Each information requirement, content-quality
expectation, or structural rule observed in S3-S6 is rewritten as
an `R-B-<wiki>-<slug>` entry in
[`catalog.md`](catalog.md), in the Phase B section. Each row uses
the trajectory format already standard there (Source, Quality dim,
Level 1, Level 2, Closure attempt, Status). Provenance is recorded
inline (which S2 observation justifies the row) so future readers
can audit. An anti-pattern field may be added in the row's
"Source" or "Notes" cell when the row is at risk of false
satisfaction.
**Output.** New rows in `catalog.md`. May supersede prior R-NN
entries (per the trajectory model's delete-on-promotion rule from
[`../phase-preliminary/architecture-method.md`](../phase-preliminary/architecture-method.md)
— a row replaced by a tighter formulation has the prior row
deleted, not flagged superseded).
**Exit criterion.** Every new R-NN cites its evidence (S2
observation OR Phase A goal). Every R-NN has a Level 1 / Level 2
gap that is testable.

### S8 — Hand to implementation

**Input.** Updated catalog + product file.
**Activity.** Implementation reviews the new R-NN rows for
testability. Mismatches go back to S7. When implementer signs off,
the bench / compiler / ingest prompts and graders are amended to
reference the R-NN IDs they serve. A Phase F experiment may be
opened
([`../phase-f-migration-planning/experiments/`](../phase-f-migration-planning/experiments/))
to close one or more rows as a coordinated batch.
**Output.** Catalog version is implicitly tagged (git commit on
forge main + downstream prompts/graders cite R-NN in their
comments).
**Exit criterion.** Implementation can write a verifier that
mechanically checks each Level 2 target.

## Re-walk policy

Per [`process.md`](process.md), requirements are re-emitted when
new evidence accumulates. For wiki products specifically:

| Event                                                                         | Re-walk steps |
|-------------------------------------------------------------------------------|---------------|
| New raw module added                                                          | S2, then S3-S7 affected |
| Quality regression that no existing R-NN explains                             | S2-S7         |
| New reader segment identified                                                 | S3-S7         |
| Anti-pattern observed in production output                                    | S7 (tighten Level 2; if necessary, supersede the row) |
| Implementation change blocked by absent requirement                           | S7            |
| Acceptance test passes but eye-read says output is bad                        | S7-S8 (the requirement is incomplete) |
| Acceptance test fails but eye-read says output is fine                        | S7-S8 (the requirement is wrong) |

## Operating rules

These layer on top of the project-wide rules in
[`process.md`](process.md):

- **Provenance over rhetoric.** A row quoting a real S2
  observation beats a beautifully-worded row with no evidence.
- **Anti-patterns are first-class.** A row at risk of false
  satisfaction (passes the test but fails on use) names ≥ 1
  anti-pattern in the row's Notes cell, calibrated against
  prior production failures.
- **Acceptance criteria are code, not prose.** "Reads naturally"
  is not a Level 2 target.
- **Implementation does not invent requirements.** If a prompt
  needs a rule that has no R-NN to cite, S7 happens first.
- **Re-read the corpus.** New evidence is the cheapest source of
  catalog improvement — when stuck, S2 again.

## Anti-patterns for the activity itself

- **Catalog as wish-list.** Rows written without S2 evidence that
  survive several reviews because no one challenges them.
- **Implementation owns the requirements.** Rows that exactly
  match what the current implementation already does — symptom of
  the activity having been informally captured.
- **Single-author capture.** Single architect writes rows that
  reflect their own reading mode only; anti-goals stay blank
  because the architect cannot imagine misreading their own work.
  Mitigation: the anti-pattern field is mandatory.

## What this activity replaces / does NOT replace

- **Replaces.** Ad-hoc prompt rules with no provenance. Quality
  regressions diagnosed as "the model is bad" instead of "which
  R-NN was violated?". Implementation choices justified by
  intuition.
- **Does not replace.** [`process.md`](process.md)'s general
  lifecycle (the Level 1 → Level 2 trajectory model, the
  delete-on-promotion rule, the catalog-row authorship). This
  file is the *front-end* (how requirements are discovered for a
  wiki specifically); `process.md` is the *back-end* (how any
  catalog row moves through the pipeline).
- **Does not replace.** The Phase F experiment-spec discipline.
  Once R-NN rows are in the catalog, closing them is a Phase F
  matter.
