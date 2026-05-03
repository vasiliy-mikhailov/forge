# Kurpatov-wiki — customer observations (CI-3 schema stub)

Per [ADR 0018 § Decision 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md):
the **full customer observations file** (with per-CO observation
classifications + verbatim persona-quoted material + per-pain
references + bucket-content enumerations) lives in the **private**
sibling repo at `kurpatov-wiki-wiki/metadata/customer-observations.md`.
Customer assessments are commercial-IP-adjacent critique and stay
private per the 2026-05-02 architect call.

This file in forge is a schema-only stub — persona-letter
mapping + CO-NN ID convention + bucket NAMES (without in-bucket-
content examples) + quality-dimension cross-references. NO
observation counts (those imply pain volume = assessment). NO
skip-share aggregates. NO bucket-content enumerations citing
specific finding classes.

This file is the CI-3 schema deliverable of the
[Wiki PM role](../../roles/wiki-pm.md) per
[`/phase-requirements-management/wiki-customer-interview.md`](../../../phase-requirements-management/wiki-customer-interview.md).
CI-4 (problem statement) and CI-5 (R-NN emission) cite
observations from the private file by ID
(`CO-NN-<persona-letter>`).

## Persona-letter mapping

CI-3 introduces a single-letter shorthand for cross-persona
cross-tab. Persona files live at
[`../../roles/customers/`](../../roles/customers/).

| Letter | Persona slug                | Reading-mode summary                                  |
|--------|------------------------------|--------------------------------------------------------|
| M      | academic-researcher          | citation-hunt; primary-source verification; chapter-grade |
| A      | entry-level-student          | linear, builds-from-zero, glossary-hungry              |
| L      | lay-curious-reader           | phone-burst, 5-10 min/sitting, 1 takeaway/lecture      |
| T      | time-poor-reader             | 12 min/lecture hard cap; TL;DR + 1 technique + 1 reframe |
| W      | working-psychologist         | clinical applicability index; ethics-aware; supervisor-eyed |

## Corpus walked metadata

- Wiki product under inspection: kurpatov-wiki product line.
- Walk scope: per the latest CI cycle (see private full file for
  module + lecture identifiers).
- Per-persona ledger tree: `kurpatov-wiki-wiki/metadata/customer-pains/<persona-slug>/<lecture-stem>.md` per [ADR 0018](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).
- Per-persona cumulative knowledge: `kurpatov-wiki-wiki/metadata/customer-pains/<persona-slug>/__knowledge.md` per [ADR 0026](../../../phase-preliminary/adr/0026-per-persona-cumulative-knowledge-and-skip-share.md).
- Walk date + counts: see private full file.

## Observation ID convention

`CO-NN-<persona-letter>` where:
- `CO` = "Customer Observation" (parallels source-side `OBS`).
- `NN` = monotonically-increasing within a CI-3 walk (zero-padded to 2).
- `<persona-letter>` = single letter from the mapping above (M/A/L/T/W);
  for cross-persona observations (≥ 2 personas), use `X` (cross-cutting).

Examples: `CO-01-X` (cross-persona observation class),
`CO-12-W` (working-psychologist-specific observation),
`CO-07-T` (time-poor-reader-specific observation).

## Bucket catalog

Customer observations classify into 4 **bucket NAMES** (parallel to
source-side Substance / Form / Air, but customer-side):

- **Pipeline** — wiki-pipeline / data / extraction defects
  surfacing as reader pain.
- **Form** — voice / format / pacing / chapter-marker / TL;DR /
  forward-backward-reference issues.
- **Concept** — concept-graph defects readers cite.
- **Substance** — what's NOT in the lectures (gaps, errors,
  outdated frameworks).

In-bucket-content examples + counts of observations per bucket
per persona live in the private full file.

## Quality dimensions referenced

Each observation tag includes ≥ 1 capability **Quality
Dimension** from
[`develop-wiki-product-line.md`](../../capabilities/develop-wiki-product-line.md):
Voice preservation · Reading speed · Dedup correctness ·
Fact-check coverage · Concept-graph quality · Reproducibility ·
Transcription accuracy · Requirement traceability.

## Cross-link

- Private full file: `kurpatov-wiki-wiki/metadata/customer-observations.md`.
- CI-4 schema stub (this directory): [`customer-problems.md`](customer-problems.md).
- Cycle definition: [`../../../phase-requirements-management/wiki-customer-interview.md`](../../../phase-requirements-management/wiki-customer-interview.md).
- Driver ADR: [`../../../phase-preliminary/adr/0016-wiki-customers-as-roles.md`](../../../phase-preliminary/adr/0016-wiki-customers-as-roles.md).
- Skip-share metric: [`../../../phase-preliminary/adr/0026-per-persona-cumulative-knowledge-and-skip-share.md`](../../../phase-preliminary/adr/0026-per-persona-cumulative-knowledge-and-skip-share.md).
- Privacy boundary: [`../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md`](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: forge needs an in-tree schema reference for CI-3
  deliverables so future architects can adopt the same Wiki PM
  customer-walk discipline for any commercial-corpus wiki product
  (per ADR 0018 privacy-boundary pattern). The assessment content
  itself stays private.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95) + TTS (KR:
  tts_share ≥ 0.30 per ADR 0026).
- **Outcome**: this stub holds CI-3 schema only; CI-4
  (`customer-problems.md`) cites CO-NN by ID; CI-5 catalog rows
  resolve P-N + CO-NN to private full content.
- **Measurement source**: customer-walk: CI-3 cross-tab (this
  schema + private full file) + per-persona pain ledgers.
- **Contribution**: this schema stub enables forge to self-document
  the CI-3 customer-walk method without exposing the
  customer-derived assessment content; ADR 0018 § 7 boundary holds.
- **Capability realised**: Develop wiki product line —
  Requirement traceability quality dimension +
  customer-development discipline (ADR 0016).
- **Function**: Hold-customer-observations-schema-public-side.
- **Element**: this file.
