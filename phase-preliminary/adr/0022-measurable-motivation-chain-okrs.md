# ADR 0022 — Measurable motivation chain (OKRs) renamed to "Measurable motivation chain (OKRs)"

## Status

Accepted (2026-05-02). Active.

## Measurable motivation chain (OKRs)
Per [P7](../architecture-principles.md):

- **Driver**: post-ADR-0019 + ADR-0021, every chain in forge has both
  an Outcome (the prose end-result) AND a Measurement source (the
  formula + current value). That's literally the OKR shape — `O =
  Outcome`, `KR = Measurement source value`. The section name
  `## Measurable motivation chain (OKRs)` undersells what the section IS now: it reads
  like loose narrative when it's actually a structured OKR per
  artifact. Fresh contributors and LLM agents loading forge as
  context lose the OKR-recognition signal.
- **Goal**: Architect-velocity (the section name should advertise
  what's measurable about it) + Audit-reliability (`grep -r
  "Measurable motivation chain (OKRs)"` returns the strict P26-conformant
  set; today's `grep -r "Measurable motivation chain (OKRs)"` would also catch
  conversational mentions).
- **Outcome**: every chain section across forge renamed to `##
  Measurable motivation chain (OKRs)`; section name now declares
  the structural contract (Outcome + Measurement source = O + KR);
  P14 / P24 / P26 / P28 updated to walk the new name.
- **Measurement source**: audit-predicate: P24 (universal motivation-
  chain coverage; latest walk = 0 FAIL after this commit's sweep).
- **Capability realised**: Architecture knowledge management
  ([`../../phase-b-business-architecture/capabilities/forge-level.md`](../../phase-b-business-architecture/capabilities/forge-level.md)).
- **Function**: Rename-section-to-advertise-OKR-structure.

## Context

OKRs (Objectives and Key Results) are the de-facto industry standard
for goal/measurement structures (Doerr, *Measure What Matters*, 2018;
Grove's original at Intel; Google's adoption). The mapping to
ArchiMate § 6.4 + forge's chain structure:

| OKR concept | ArchiMate § 6 element | Forge bullet |
|---|---|---|
| **Objective** (qualitative direction) | Goal | `**Goal**:` |
| **Objective** (concrete end-state) | Outcome | `**Outcome**:` |
| **Key Result** (quantitative, time-bound) | (no native ArchiMate element) | `**Measurement source**:` value (per ADR 0019) |

The chain section as it exists today is one OKR per artifact:
- O₁ = Goal (high-level direction)
- O₂ = Outcome (specific end-state for this artifact)
- KR = Measurement source value (the metric the audit reads)

Calling it `## Measurable motivation chain (OKRs)` is technically correct (the chain
IS in the Motivation aspect per ArchiMate § 6) but undersells the
measurability discipline. `## Measurable motivation chain (OKRs)`
keeps the ArchiMate-aspect framing AND signals the OKR structure
to anyone who knows that vocabulary.

## Decision

### 1. Section heading renamed everywhere

All 60 files with `## Measurable motivation chain (OKRs)` and all 17 ADRs with
`## Motivation` are renamed to:

```
## Measurable motivation chain (OKRs)
```

Carve-out: `## Motivation Domain` in
[`phase-preliminary/archimate-language.md`](../archimate-language.md)
is NOT renamed — that's an ArchiMate-spec § 6 section reference, not
a per-file chain. (P24 + P26 walkers already exclude it via the
strict regex.)

### 2. P14 / P24 / P26 / P28 signals updated

The four predicates that walk the chain regex grep for the new
heading. P24's signal becomes:

```
^## Measurable motivation chain \(OKRs\)\s*$  OR
(?:^|\n)Transitive coverage:
```

The old `^## Measurable motivation chain (OKRs)` and bare `^## Motivation` patterns
are removed (no backward-compat, per delete-on-promotion).

### 3. Tooling updated in same commit

`scripts/test-runners/motivation-measurability-report.py`,
`contribution-report.py`, and `quality-report.py` all get their
chain regexes updated. Re-run after sweep: 0 P26 gaps + 0 P28 fails
+ 1 prune candidate (architect-deferred tarasov-wiki).

### 4. Body-text references swept

Every prose mention of "Measurable motivation chain (OKRs)" / "measurable motivation chain (OKRs)" in
audit findings, ADRs, READMEs, runner docstrings is rewritten to
"Measurable motivation chain (OKRs)" or "OKR chain" (where context
allows the shorter form). Audit md files for prior walks
(2026-04-30 → 2026-05-01y) are NOT rewritten — they're historical
record per the audit-cycle's append-only invariant.

### 5. ADR template updated

ADR 0017 § Decision 3 ("ADR template gains required Motivation
section") is amended via this ADR's Decision 5: future ADRs (0023+)
use `## Measurable motivation chain (OKRs)` directly, not
`## Motivation`.

### 6. ADR 0019's table heading update

ADR 0019's § Decision 1 references "every measurable motivation chain (OKRs) Outcome
cites a measurement source" — wording stays (the chain IS the
motivation; only the section heading changes). The table itself
(citation types) is untouched.

## Consequences

- **Plus**: section name now self-documents the OKR structure;
  no need to read ADR 0019 to know what the section is for.
- **Plus**: industry-standard vocabulary makes forge more legible
  to contributors familiar with OKR practice.
- **Plus**: stricter regex (`grep -r "## Measurable motivation
  chain"`) returns only the strict-conformant set; fewer false
  positives in audits.
- **Minus**: every artifact touched in same commit; large diff. One
  audit walk cost. Mitigation: same predicate-+-sweep-+-same-commit
  pattern as ADR 0017 / 0019 / 0021.
- **Minus**: heading is longer (33 chars vs. 19 for "Motivation
  chain"); minor cost in line-length terms.
- **Minus**: external readers familiar with ArchiMate but not OKRs
  need a one-line gloss. Mitigation: this ADR provides the mapping
  table.

## Invariants

- A new artifact landing in forge using `## Measurable motivation chain (OKRs)` or
  `## Motivation` (instead of `## Measurable motivation chain (OKRs)
  (OKRs)`) is a P24 FAIL on the next audit walk.
- The carve-out for `## Motivation Domain` (ArchiMate spec section
  reference) is preserved by the strict-regex pattern; no opt-in
  needed.
- Future ADRs (0023+) MUST use `## Measurable motivation chain (OKRs)
  (OKRs)` per the ADR-0017-Decision-3 amendment in this ADR's
  Decision 5.

## Alternatives considered

- **Add an `## OKR` subsection inside `## Measurable motivation chain (OKRs)`**
  (keep both names). Rejected: redundancy violates delete-on-promotion;
  the section IS the OKR — name it that.
- **Rename to `## OKRs` only** (drop "Motivation" entirely).
  Rejected: loses the ArchiMate-aspect anchoring (P7 + ADR 0017 says
  Motivation spans every layer; the section name should keep that
  word). The compound name preserves both anchors.
- **Rename to `## Objectives and Key Results`** (spell it out).
  Rejected: the parenthetical `(OKRs)` form is the standard Doerr-era
  shortening; spelling it out reads more formal than necessary.
- **Per-file opt-in to the new name** (gradual migration).
  Rejected: same reason as ADR 0017's all-at-once sweep — partial
  migration creates a P24 ambiguity (which name is canonical?) that
  costs more architect-velocity than the one big diff.

## Follow-ups

- ADR 0017's § Decision 3 amended in same commit (template language
  update).
- ADR 0019's worked-example sentence ("when a chain has
  `**Measurement source**: runner: test-wiki-pm-runner`...") gets a
  small clarification that "chain" now refers to the renamed section.
- Future quarterly review: any other section names in forge that
  could benefit from a similar self-documenting rename? Candidates:
  `## Decision` (ADRs), `## Reward` (test md). Out of scope for
  this ADR.
