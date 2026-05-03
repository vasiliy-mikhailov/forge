# Kurpatov-wiki — customer problems (CI-4 schema stub)

Per [ADR 0018 § Decision 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md):
the **full CI-4 problem statement** (with P-N named problem
content + severity / evidence / recommended-action / closure
specifics) lives in the **private** sibling repo at
`kurpatov-wiki-wiki/metadata/customer-problems.md`. Customer
assessments of the wiki product (which transitively assess the
underlying Kurpatov course) are commercial-IP-adjacent critique
and stay private per the 2026-05-02 architect call.

This file in forge is a schema-only stub — severity-coding
table, affected-persona shorthand, recommended-action mapping
schema. NO P-N problem statements. NO assessment content.

This file is the CI-4 deliverable schema of the
[Wiki PM role](../../roles/wiki-pm.md) per
[`/phase-requirements-management/wiki-customer-interview.md`](../../../phase-requirements-management/wiki-customer-interview.md).

## Cross-link

- Schema stub (this directory): [`customer-observations.md`](customer-observations.md).
- Private full file (this CI-4 deliverable): `kurpatov-wiki-wiki/metadata/customer-problems.md`.
- Cycle definition: [`../../../phase-requirements-management/wiki-customer-interview.md`](../../../phase-requirements-management/wiki-customer-interview.md).
- Privacy boundary: [`../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md`](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

## Severity coding (schema only)

- **CRITICAL** — blocking-severity for ≥ 2 personas; affects
  any reading-mode use of the wiki; needs R-NN row at OPEN
  status (architect-approved) before next K-experiment.
- **HIGH** — blocking-severity for 1 persona OR moderate for
  ≥ 3; needs R-NN row at PROPOSED status; review with
  architect.
- **MEDIUM** — moderate-severity for ≥ 2 personas, no
  blocking; backlog candidate.
- **Substance-magnitude override** (queued amendment per
  Wiki PM self-assessment): a single-persona assessment
  finding may be elevated to CRITICAL if it has cross-corpus
  consequence (e.g. pedagogy/practice mismatch
  invalidating prior teaching). Architect-approved
  case-by-case until codified.

## Affected-persona shorthand

M = academic-researcher; A = entry-level-student; L = lay-curious-reader;
T = time-poor-reader; W = working-psychologist.

## Recommended-action mapping schema

| Problem (P-N) | Proposed R-NN slug                | Quality dim                        | Source cell                       |
|---------------|------------------------------------|------------------------------------|-----------------------------------|
| see private full file | `R-B-<discipline-slug>` | from develop-wiki-product-line.md | `customer:<persona-letter>` tags  |

CI-5 R-NN row drafts (architect review pending) at
`/sessions/.../mnt/outputs/CI-5-rnn-draft.md`. Once approved,
rows land in
[`../../../phase-requirements-management/catalog.md`](../../../phase-requirements-management/catalog.md)
with Level-1/2/Closure cells citing P-N and CO-NN IDs (which
resolve to private full content) rather than inline assessment
text.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: forge needs an in-tree schema reference for CI-4
  deliverables so future architects can adopt the same
  discipline for any commercial-corpus wiki product (per
  ADR 0018 privacy-boundary pattern). The assessment content
  itself stays private.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95) — fixing the
  problems documented in the private file improves wiki
  quality; this stub keeps the schema discoverable.
- **Outcome**: this stub holds severity coding + affected-persona
  shorthand + recommended-action mapping schema; private full
  file holds P-N statements; CI-5 catalog rows cite P-N IDs.
- **Measurement source**: customer-walk: CI-3 cross-tab feeds
  CI-4 problem statement; loop closure measured by post-fix
  re-walk (CI-7 per ADR 0016 § Steps).
- **Contribution**: this schema stub enables forge to
  self-document the CI-4 discipline without exposing the
  customer-derived assessment content; commercial-IP boundary
  per ADR 0018 § 7 holds.
- **Capability realised**: Develop wiki product line —
  Requirement traceability quality dimension +
  customer-development discipline.
- **Function**: Hold-customer-problems-schema-public-side.
- **Element**: this file.
