# Kurpatov-wiki — customer observations (schema stub)

Per [ADR 0018](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md):
the **full customer observations file** (with persona-voice
quotes paraphrasing Курпатов content + per-pain
classifications) lives in the **private** sibling repo at
`kurpatov-wiki-wiki/metadata/customer-observations.md`. This
file in forge is a schema-only stub — observation IDs +
buckets + dimensions + counts + persona-letter mapping. NO
verbatim Курпатов excerpts. NO persona-quoted content that
would let a reader reconstruct lecture material.

This file is the CI-3 output of the
[Wiki PM role](../../roles/wiki-pm.md) per
[`/phase-requirements-management/wiki-customer-interview.md`](../../../phase-requirements-management/wiki-customer-interview.md).
CI-4 (problem statement) and CI-5 (R-NN emission) cite
observations from the private file by ID
(`CO-NN-<persona-letter>`).

The capability dimensions referenced in observation tags come
from
[`/phase-b-business-architecture/capabilities/develop-wiki-product-line.md`](../../capabilities/develop-wiki-product-line.md):
**Voice preservation**, **Reading speed**, **Dedup correctness**,
**Fact-check coverage**, **Concept-graph quality**,
**Reproducibility**, **Transcription accuracy**,
**Requirement traceability**.

## Persona-letter mapping

CI-3 introduces a single-letter shorthand for cross-persona
cross-tab. Persona files live at
[`../../roles/customers/`](../../roles/customers/).

| Letter | Persona slug                | Working tag       | Reading-mode summary                                  |
|--------|------------------------------|-------------------|--------------------------------------------------------|
| M      | academic-researcher          | Marina (Dr. М.)   | citation-hunt; primary-source verification; chapter-grade |
| A      | entry-level-student          | Аня               | linear, builds-from-zero, glossary-hungry              |
| L      | lay-curious-reader           | Антон-designer    | phone-burst, 5-10 min/sitting, 1 takeaway/lecture      |
| T      | time-poor-reader             | Антон-PM          | 12 min/lecture hard cap; TL;DR + 1 technique + 1 reframe |
| W      | working-psychologist         | Анна С.           | clinical applicability index; ethics-aware; supervisor-eyed |

## Corpus walked (CI-1)

- Wiki under inspection: `kurpatov-wiki-raw` modules `000 Путеводитель по программе` + `001 Глубинная психология и психодиагностика в консультировании` (44 lecture stems).
- Per-persona ledger tree: `kurpatov-wiki-wiki/metadata/customer-pains/<persona-slug>/<lecture-stem>.md` (220 ledgers total) per [ADR 0018](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).
- Per-persona cumulative knowledge: `kurpatov-wiki-wiki/metadata/customer-pains/<persona-slug>/__knowledge.md` per [ADR 0026](../../../phase-preliminary/adr/0026-per-persona-cumulative-knowledge-and-skip-share.md).
- Walk date: 2026-05-02 (CI-2 sweep complete; this file is the CI-3 cross-tab).

## Observation ID convention

`CO-NN-<persona-letter>` where:
- `CO` = "Customer Observation" (parallels source-side `OBS`).
- `NN` = monotonically-increasing within this CI-3 walk (zero-padded to 2).
- `<persona-letter>` = single letter from the mapping above (M/A/L/T/W); for cross-persona observations (≥ 2 personas), use `X` (cross-cutting).

Examples: `CO-01-X` (cross-persona pipeline-bug class), `CO-12-W`
(working-psychologist-specific clinical-ethics finding),
`CO-07-T` (time-poor-reader-specific TL;DR-density observation).

## Observation count totals (today)

| Persona letter | Pains (blocking) | Pains (moderate) | Pains (mild) | Total ledger entries |
|---|---|---|---|---|
| M (academic-researcher)    |  66 | 142 |  90 | 298 |
| A (entry-level-student)    |  64 | 152 | 120 | 336 |
| L (lay-curious-reader)     |  33 |  72 |  86 | 191 |
| T (time-poor-reader)       |  41 |  79 |  72 | 192 |
| W (working-psychologist)   |  65 | 128 |  43 | 236 |
| **corpus**                 | **269** | **573** | **411** | **1253** |

Per-persona corpus mean `would_skip_share` (per ADR 0026):

| Persona | Mean skip-share | Distribution character |
|---|---|---|
| A — entry-level-student     | 0.41 | linear builder; least redundancy perceived |
| M — academic-researcher     | 0.54 | bimodal — bulk 0.45–0.60 + outliers (2 × 1.00, 1 × 0.30) |
| W — working-psychologist    | 0.55 | typical 0.45–0.65 with 1.00 stubs/dups |
| L — lay-curious-reader      | 0.57 | 18% lectures usable out-of-box; rest needs compression |
| T — time-poor-reader        | 0.64 | text-format 0.50; audio-format 0.78; first-half 0.55, second-half 0.72 |

CI-3 cross-tab observation count (this file): **34**
distinct observations, of which **18 cross-persona (X-letter,
≥ 2 persona votes)** and **16 persona-specific (single-letter,
1 persona vote)**. See private full file for per-CO classification.

## Bucket / dimension catalog

Customer observations classify into 4 **buckets** (parallel to
source-side Substance / Form / Air, but customer-side):

- **Pipeline** — wiki-pipeline / data / extraction defects
  surfacing as reader pain (duplicate stems, empty html
  wrappers, whisper-VAD degradation, missing-attachment
  extraction, ambiguous prefix numbering). Cross-persona by
  construction: every persona walked the same pipeline.
- **Form** — voice / format / pacing / chapter-marker / TL;DR
  / forward-backward-reference issues that affect
  comprehension or skim speed. Persona-sensitive: time-poor
  vs deep-reader weight different.
- **Concept** — concept-graph defects readers cite: undefined
  authors, terms-without-context, density spikes,
  attribution-voids, missing primary-source citations,
  missing forward links to definitions.
- **Substance** — what's NOT in the lectures: factual-error
  candidates, outdated-frameworks-rendered-as-current-science,
  curriculum gaps, ethics-violation-modeling, pedagogy /
  practice mismatch. The "substance gaps" the corpus does not
  itself surface.

Each observation tag includes ≥ 1 capability **Quality
Dimension** from
[`develop-wiki-product-line.md`](../../capabilities/develop-wiki-product-line.md):
Voice preservation · Reading speed · Dedup correctness ·
Fact-check coverage · Concept-graph quality · Reproducibility ·
Transcription accuracy · Requirement traceability.

## Cross-persona vote distribution

CI-3 cross-tab, by ID (counts only — no content):

| ID | Bucket | Personas voting | Severity (max across personas) |
|---|---|---|---|
| CO-01-X | Pipeline | M, A, L, T, W (5/5) | blocking |
| CO-02-X | Pipeline | M, A, L, T, W (5/5) | blocking |
| CO-03-X | Pipeline | M, A, L, T, W (5/5) | blocking |
| CO-04-X | Pipeline | M, T (2/5) | blocking |
| CO-05-X | Pipeline | M, T, W (3/5) | moderate |
| CO-06-X | Concept  | M, A, L, T, W (5/5) | blocking |
| CO-07-X | Concept  | M, A, T, W (4/5) | blocking |
| CO-08-X | Concept  | M, A (2/5) | moderate |
| CO-09-X | Form     | A, L, T (3/5) | blocking |
| CO-10-X | Form     | M, A, L, T, W (5/5) | moderate |
| CO-11-X | Form     | A, L, T (3/5) | moderate |
| CO-12-X | Form     | A, T (2/5) | moderate |
| CO-13-X | Form     | L, T (2/5) | moderate |
| CO-14-X | Substance| M, W (2/5) | blocking |
| CO-15-X | Substance| M, W (2/5) | blocking |
| CO-16-X | Substance| M, W (2/5) | blocking |
| CO-17-X | Substance| M, A, W (3/5) | moderate |
| CO-18-X | Substance| L, T (2/5) | moderate |
| CO-19-M | Concept  | M (1/5)   | blocking | (academic primary-source citation depth) |
| CO-20-M | Substance| M (1/5)   | blocking | (post-Freudian-evolution void; Russian-genealogy attribution void) |
| CO-21-A | Concept  | A (1/5)   | blocking | (forward/backward-ref-without-anchor frequency) |
| CO-22-A | Form     | A (1/5)   | moderate | (genre-mixing — lecture/methodology/case/session unmarked) |
| CO-23-A | Substance| A (1/5)   | moderate | (СПП vs university-curriculum overlap unspecified) |
| CO-24-L | Form     | L (1/5)   | blocking | (audio length without chapter markers; phone-burst incompatible) |
| CO-25-L | Form     | L (1/5)   | moderate | (lecture lacks one-line summary at end) |
| CO-26-L | Form     | L (1/5)   | moderate | (case-first vs theory-first ordering preference) |
| CO-27-T | Form     | T (1/5)   | blocking | (buried-lede pattern; TL;DR-header absence) |
| CO-28-T | Form     | T (1/5)   | moderate | (audio-recap-of-text-pair without compression) |
| CO-29-T | Form     | T (1/5)   | moderate | (workbook bundled with lecture without H3 marker) |
| CO-30-W | Substance| W (1/5)   | blocking | (15 ethics-action-level issues; structural pattern) |
| CO-31-W | Substance| W (1/5)   | blocking | (pedagogy/practice mismatch — L42 live demo) |
| CO-32-W | Substance| W (1/5)   | blocking | (curriculum gaps inventory: defenses / modern relational / trauma research / EBP / IPV / etc.) |
| CO-33-W | Substance| W (1/5)   | moderate | (outdated frameworks rendered as current science: catharsis, Penisneid as causal, гомосексуальность-как-отклонение) |
| CO-34-W | Substance| W (1/5)   | moderate | (peer-practice TAT — projective method without supervised training) |

**Cross-persona (X) observations: 18.** Per CI-3 rule of
strength: ≥ 2 personas → "strong signal, likely real wiki
defect" → R-NN with `Status: PROPOSED`.

**Persona-specific observations: 16.** Single-persona-vote →
R-NN with `Status: PROPOSED-PERSONA-SPECIFIC`. Architect
decides whether to ship a single-segment fix.

## Bucket totals

| Bucket    | Cross-persona (X) | Persona-specific | Total |
|-----------|---|---|---|
| Pipeline  |  5 |  0 |  5 |
| Concept   |  3 |  3 |  6 |
| Form      |  5 |  6 | 11 |
| Substance |  5 |  7 | 12 |
| **total** | **18** | **16** | **34** |

## Dimension distribution (raw mentions across the 220 ledgers)

| Dimension              | M (acad) | A (stud) | L (lay) | T (PM) | W (psy) | Total |
|-----------------------|---|---|---|---|---|---|
| Concept-graph quality | 127 | 228 |   0 |  66 |  39 | 460 |
| Fact-check coverage   | 209 |  26 |   1 |   0 | 152 | 388 |
| Voice preservation    |  30 | 104 | 124 |  50 |  49 | 357 |
| Reproducibility       |  43 |   5 |   0 |   1 |  85 | 134 |
| Reading speed         |   7 |   5 |   5 |  88 |  19 | 124 |
| Requirement traceab.  |  74 |   8 |   0 |   0 |   1 |  83 |
| Transcription accur.  |  22 |  13 |   8 |   6 |   6 |  55 |
| Dedup correctness     |   9 |   6 |   6 |   5 |   6 |  32 |

Reads: Concept-graph and Fact-check dominate;
Concept-graph is the broadest cross-persona pain signal;
Fact-check is concentrated in M+W (the two primary-source-
literate personas); Voice is the lay/student pain
(comprehension, not citation); Reading speed lives almost
entirely in T (PM hard cap drives it); Reproducibility is
W's clinical-ethics column.

## Cross-link to private full file

Private repo: `kurpatov-wiki-wiki/metadata/customer-observations.md`.

The private file carries:
- Per-CO verbatim persona-voice text (Russian, paraphrasing Курпатов content where relevant).
- Per-CO lecture-stem references with segment ranges.
- Per-CO bucket/dimension classification reasoning.
- The five `__knowledge.md` chain summaries cited for
  cumulative-pattern observations.

Tools that need verbatim access default to the private path
via the `_find_repo` helper (parallel to source-side
corpus-observations).

## Why split

Per [ADR 0018](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md):
the 220 pain ledgers contain Russian-language paraphrases of
Курпатов lecture content (e.g. an Аня pain entry naming a
specific Курпатов phrase with its segment range) — this is
sufficient for a reader to reconstruct material content. The
private repo holds those paraphrases; this forge stub holds
only the schema (ID convention, bucket catalog, dimension
catalog, count totals, persona-letter mapping, cross-persona
vote distribution).

## Measurable motivation chain
Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: forge needs an in-tree schema reference for
  CI-4 (problem statement) and CI-5 (R-NN emission) to cite
  CO-NN by ID without exposing customer-side paraphrase
  content (per ADR 0018 privacy boundary). This file
  parallels the source-side `corpus-observations.md` stub.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95) + TTS
  (KR: tts_share ≥ 0.30 per ADR 0026).
- **Outcome**: this stub holds schema + cross-link to private;
  CI-4 problem statement (`customer-problems.md` in this
  directory) and CI-5 R-NN rows in
  [`catalog.md`](../../../phase-requirements-management/catalog.md)
  cite CO-NN IDs without forge ever loading
  persona-quoted Курпатов content.
- **Measurement source**: customer-walk: CI-3 cross-tab
  (this file) + private full file at
  `kurpatov-wiki-wiki/metadata/customer-observations.md`;
  feeds CI-4 problem statement and CI-5 R-NN trajectory rows.
- **Contribution**: each cross-persona observation drives one
  R-NN row; loop closure measured by post-fix re-walk
  (CI-7 per ADR 0016 § Steps).
- **Capability realised**: Develop wiki product line
  ([`../../capabilities/develop-wiki-product-line.md`](../../capabilities/develop-wiki-product-line.md))
  — Requirement traceability quality dimension +
  customer-development discipline (ADR 0016).
- **Function**: Hold-customer-observations-schema-public-side.
- **Element**: this file.
