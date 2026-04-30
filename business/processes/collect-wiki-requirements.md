# Process — Collect Wiki Requirements

**TOGAF Phase B — Business Process.**

Operationalises the
[Wiki Requirements Collection capability](../capabilities/wiki-requirements-collection.md),
owned by the
[Wiki Product Manager role](../roles/wiki-product-manager.md).

## Trigger

Any of:

- A new wiki product is being planned in forge.
- An existing wiki product has accumulated complaints / regressions
  that point to missing or wrong requirements.
- A new module of source material is added to an existing wiki and
  may carry stakeholders or content requirements not in the
  current catalogue.
- A pipeline change cannot be made cleanly because the requirement
  it would serve is not in the catalogue.

## Participants

| Participant | Role in this process |
|-------------|----------------------|
| Wiki Product Manager | Drives the process, owns deliverables. |
| Operator | Provides stakeholder evidence beyond what corpus shows. Approves catalogue versions. |
| Pipeline implementer (consultative) | Reviews acceptance criteria for testability before they're frozen. |

## Inputs

- Raw corpus for the wiki (read-only).
- Existing artifacts of the wiki, if any (frontmatter, prompts,
  past evals).
- Existing decision records (`docs/adr/`) constraining the wiki.

## Output deliverables

Produced under `products/<wiki>/`:

1. `stakeholders.md` — Stakeholder Map
2. `goals-and-drivers.md` — Goals & Drivers Catalogue
3. `use-cases.md` — Use-Case Catalogue
4. `information-architecture.md` — Information Architecture
5. `requirements-catalogue.md` — Requirements Catalogue
6. `quality-attributes.md` — Quality Attribute List
7. `traceability.md` — Traceability Matrix

## Steps

Numbered. Each step lists what it consumes, what it produces, and
its exit criterion. Steps are not strictly sequential — early
steps can be revisited as later steps surface evidence — but a
later step cannot pass exit criteria if its earlier dependency
hasn't.

### Step 1 — Sample and pre-read corpus

**Input.** Raw corpus.
**Activity.** Pick ≥ 5 representative raws spanning format, length,
and content-area variation. Read each once with no rule in mind —
absorb voice, density, structure variation. No notes yet.
**Output.** A list of sampled file paths and brief structural
notes per sample.
**Exit criterion.** Can answer: "what are the major formats this
wiki must handle, and which raws represent them?"

### Step 2 — Inventory observations

**Input.** Step 1 output + the raws themselves.
**Activity.** For each raw, write quoted observations into three
buckets:
- **Substance** — actual content the source conveys.
- **Form** — recurring patterns of voice, structure, transitions.
- **Air** — material that, when removed, doesn't change the
  substance.
Keep quotes verbatim with file:line references.
**Output.** `corpus-observations.md` (working file, may not survive
into the final deliverables — its content is the *evidence* that
later steps cite).
**Exit criterion.** Each of the 5+ raws has at least 5 quoted
observations across the three buckets.

### Step 3 — Identify stakeholders

**Input.** Step 2 substance bucket + operator input.
**Activity.** For each substance observation, ask: *who needs this
content, in what form, for what task?* Aggregate recurring
audience profiles into stakeholder segments. Operator confirms
the segments correspond to real intended audiences (not artifact
of corpus alone).
**Output.** `stakeholders.md` with one entry per segment:
```
SH-NN  Name
       Goals  (what they want to do with the wiki)
       Reading mode  (look-up | sequential study | cross-reference | skim)
       Information needs  (what specifically must be findable)
       Anti-goals  (what would actively hurt them)
       Evidence  (which Step-2 observations or operator inputs support this)
```
**Exit criterion.** Every segment has ≥ 2 evidence pointers.
Anti-goals are not blank.

### Step 4 — Decompose stakeholder goals into product goals

**Input.** `stakeholders.md`.
**Activity.** For each Stakeholder Goal, write the wiki-product-
level goals it implies. The product goal must be specific to *the
wiki* (e.g. "a student preparing for an exam can find the
definition of a concept in under 10 seconds and verify which
lecture introduced it"), not the upstream organisational goal
(e.g. "students become competent therapists").
**Output.** `goals-and-drivers.md`:
```
G-NN   Goal
       Stakeholder(s) served  (SH-NN refs)
       Driver  (why this goal exists in the project)
       Success criterion  (when is it met?)
       Anti-pattern  (what would falsely look like meeting it?)
```
**Exit criterion.** Every G-NN cites ≥ 1 SH-NN. Every G-NN has an
anti-pattern.

### Step 5 — Walk use cases

**Input.** `stakeholders.md` + `goals-and-drivers.md`.
**Activity.** For each (Stakeholder, Goal) pair, walk concrete steps
the reader takes. Each step lists the information they need at that
step.
**Output.** `use-cases.md`:
```
UC-NN  Name
       Actor  (SH-NN)
       Trigger
       Steps  (numbered, each with: action — information consumed)
       Success outcome
       Failure modes
```
**Exit criterion.** Every G-NN is reachable from ≥ 1 UC. Every UC
cites ≥ 1 SH-NN.

### Step 6 — Define information architecture

**Input.** Use-cases (which surface entity references) + existing
wiki schema, if any.
**Activity.** Codify the wiki's entity model: entities, attributes,
relations, cardinalities, existence rules. Where the wiki already
has a schema, document it; where use-cases need a new entity or
attribute, propose the addition.
**Output.** `information-architecture.md`:
```
Entity  Name
        Attributes  (with types and constraints)
        Relations  (entity → entity, with cardinality and direction)
        Existence rules  (which entities must exist; which can be optional)
        Use-case refs  (which UCs depend on this entity / attribute)
```
**Exit criterion.** Every attribute is referenced by ≥ 1 UC, OR
explicitly justified as structural metadata (e.g. provenance
fields).

### Step 7 — Distill requirements

**Input.** All prior outputs + Step 2 evidence file.
**Activity.** Each information requirement, content-quality
expectation, or structural rule observed in steps 3-6 is rewritten
as an `R-NN` entry in the catalogue. Where two observations
collapse into one requirement, do that. Where one observation
splits into multiple, do that. The result is a requirement set
that *implies* the use-cases plus the information architecture.
**Output.** `requirements-catalogue.md`:
```
R-NN   Type  (functional | quality | structural | provenance)
       Title
       Statement  (testable claim)
       Rationale  (UC / G / SH refs)
       Source evidence  (Step-2 observation refs, with quotes)
       Acceptance criterion  (function over (input, output) → pass | fail)
       Anti-pattern  (≥ 1 way it could be falsely satisfied)
       Owner  (which pipeline stage is responsible)
       Status  (proposed | accepted | superseded)
```
**Exit criterion.** Every R-NN has provenance. Every R-NN has a
testable acceptance criterion. Every R-NN has an anti-pattern.

### Step 8 — Identify quality attributes

**Input.** All prior outputs.
**Activity.** Cross-cutting non-functional properties that apply
globally, not per-artifact, become QA-NN entries. Targets are
calibrated against the corpus (e.g. compression ratio bands
calibrated by reading raw vs human-edited summary).
**Output.** `quality-attributes.md`:
```
QA-NN  Quality attribute
       Description
       Measure  (the function that returns a number / bool)
       Target  (passing threshold)
       How enforced  (which pipeline stage / verifier check)
```
**Exit criterion.** Every QA-NN has a measure. Every QA-NN has a
target value (not just "should be high"). Every QA-NN cites the
calibration evidence behind its target.

### Step 9 — Build traceability matrix

**Input.** All prior outputs.
**Activity.** Single table whose rows are R-NN and QA-NN, columns
are SH-NN / G-NN / UC-NN. Mark which stakeholders / goals /
use-cases each requirement traces to. Highlight orphans
(requirements with no UC; use-cases with no requirement;
stakeholders with no goal).
**Output.** `traceability.md` with the matrix and an explicit
list of orphans.
**Exit criterion.** Either no orphans, or every orphan has a
documented disposition (pending evidence / superseded / accepted
exception).

### Step 10 — Hand to implementation

**Input.** Frozen v1 of all deliverables.
**Activity.** Implementer reviews acceptance criteria for
testability. Mismatches go back to step 7. When implementer
signs off, the catalogue version is tagged.
**Output.** A tagged commit + a hand-off note in the relevant
implementation repo (e.g. wiki-bench) referencing the tag.
**Exit criterion.** Implementer can write a verifier that mechanically
checks all acceptance criteria.

## Re-walk policy

The process is not one-shot. Triggers for re-walking specific
steps:

| Event | Re-walk steps |
|-------|---------------|
| New raw module added | 2, then any of 3-9 affected |
| New stakeholder identified | 3-9 |
| Use-case found that no current R-NN supports | 5-7 |
| Acceptance criterion fails on a real artifact AND eye-read agrees the artifact is good | 7-8 (the requirement is wrong) |
| Acceptance criterion passes on an artifact AND eye-read says the artifact is bad | 7-8 (the requirement is incomplete) |
| Anti-pattern observed in production output | 7 (add anti-pattern to relevant R-NN; consider tightening criterion) |

Every re-walk produces a catalogue version bump with a changelog
entry. Old versions are not deleted; superseded requirements stay
visible with `Status: superseded by R-NN`.

## Operating rules

- **Provenance over rhetoric.** Drop unsourced requirements rather
  than rewrite them prettier.
- **Anti-patterns are first-class.** A requirement without an
  anti-pattern is incomplete.
- **Acceptance criteria are code, not prose.** "Reads naturally"
  is not in the catalogue.
- **Implementation does not invent requirements.** New rule needed
  in a prompt → new R-NN in the catalogue first.
- **Re-read the corpus.** New evidence is the cheapest source of
  catalogue improvement.

## What this process replaces

- Hand-wavy "quality contract" lists (e.g. wiki-bench ADR 0013's
  list of properties bench_grade doesn't check) become
  `quality-attributes.md` entries with measures and targets.
- Ad-hoc prompt rules become R-NN-cited prompt rules.
- Eval failures become R-NN traceback ("which requirement did
  this output violate?") instead of "the model is bad."
