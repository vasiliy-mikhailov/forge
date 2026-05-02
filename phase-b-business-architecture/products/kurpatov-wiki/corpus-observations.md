# Kurpatov-wiki — corpus observations (schema stub)

Per [ADR 0018](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md):
the **full corpus observations file** (with Cyrillic verbatim
quotes from Курпатов lectures) lives in the **private**
sibling repo at
`kurpatov-wiki-wiki/metadata/corpus-observations.md`. This
file in forge is a schema-only stub — observation IDs +
buckets + dimensions + counts, no excerpts.

This file is the S1+S2 output of the
[Wiki PM role](../../roles/wiki-pm.md) per
[`/phase-requirements-management/wiki-requirements-collection.md`](../../../phase-requirements-management/wiki-requirements-collection.md).
S3–S7 cite observations from the private file by ID
(`OBS-<source-letter>-NNN`).

The capability dimensions referenced in observation tags come
from
[`/phase-b-business-architecture/capabilities/develop-wiki-product-line.md`](../../capabilities/develop-wiki-product-line.md):
**Voice preservation**, **Reading speed**, **Dedup correctness**,
**Fact-check coverage**, **Concept-graph quality**,
**Reproducibility**, **Transcription accuracy**,
**Requirement traceability**.

## Source-letter mapping

(Identifies which `raw.json` each source letter refers to;
file paths are public — the *content* lives private.)

| Letter | raw.json path (under `kurpatov-wiki-raw/data/Психолог-консультант/`) | Module | Format |
|---|---|---|---|
| A | `000 Путеводитель по программе/000 Знакомство…/raw.json` | 000 | spoken, ~88 min, ~9 963 words |
| B | `000 Путеводитель по программе/002 Вводная лекция…/raw.json` | 000 | written конспект (PDF→text), ~3 391 words |
| C | `005 Природа внутренних конфликтов…/000 Вводная лекция. Базовые биологические потребности…/raw.json` | 005 | spoken, module 005 intro |
| D | `005 Природа внутренних конфликтов…/001 №1. Базовая социальная потребность…/raw.json` | 005 | spoken, module 005 #1 |

## Observation count totals (today)

| Source letter | Substance | Form | Air | Total |
|---|---|---|---|---|
| A (lecture A — module 000) | 4 | 7 | 9 | 20 |
| B (konspekt — module 000) | 1 | 0 | 0 | 1 |
| C (module 005 intro) | 1 | 0 | 0 | 1 |
| D (module 005 #1) | 1 | 0 | 0 | 1 |
| sub-total (cited summary table) | 7 | 7 | 9 | 23 |
| total declarations (full file) | — | — | — | 30 |

(Per audit-2026-05-01p F1: full file has 30 OBS-X-NNN
declarations; the recall harness pins 20 to source A.)

## Bucket / dimension catalog

Per the Wiki PM's S2 step:

- **Substance** — actual content the source conveys
  (Definitions, Claims, Attributions). Must survive both the
  condense step and the fact-check step intact.
- **Form** — voice signature material (branded methods,
  scenario framing, synonym chains, direct address). Lossy to
  drop; the persona file's reading-mode determines whether to
  preserve.
- **Air** — filler patterns (triple-trail и-так-далее,
  spoken-word-doubling, self-Q&A scaffolding, vocalised
  hesitations, discourse markers). Carries no information
  beyond the surrounding Substance / Form.

Each observation tag includes one or more capability
**Quality Dimensions** (from
[`develop-wiki-product-line.md`](../../capabilities/develop-wiki-product-line.md)):
Voice preservation · Reading speed · Dedup correctness ·
Fact-check coverage · Concept-graph quality · Reproducibility ·
Transcription accuracy · Requirement traceability.

## Where the verbatim content lives

Private repo: `kurpatov-wiki-wiki/metadata/corpus-observations.md`.

Tools that need verbatim access (e.g.
[`measure-corpus-recall.py`](../../../scripts/test-runners/measure-corpus-recall.py))
default to the private path via the `_find_repo` helper.

## Why split

Per [ADR 0018](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md):
forge is a public repo (`vasiliy-mikhailov/forge` on GitHub);
Курпатов's lecture content is the architect's commercial IP
and must not appear in the public tree. The split keeps:

- The **methodology** (S1+S2 process, observation schema,
  bucket / dimension catalog, OBS-NNN ID convention,
  source-letter mapping, count totals) **public** — useful for
  any architect adopting the same Wiki PM cycle for a
  different corpus.
- The **content** (Cyrillic verbatim quotes, per-OBS
  classifications) **private** — sits with the curated
  source.md / concept.md outputs in `kurpatov-wiki-wiki`.

## Motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: forge needs an in-tree schema reference for
  S3–S7 to cite OBS-X-NNN by ID without exposing content
  (per ADR 0018 privacy boundary).
- **Goal**: Architect-velocity (one place to look up the
  schema) + IP protection (no excerpts in public).
- **Outcome**: this stub holds schema + cross-link to private;
  audit predicates (P11, P25 queued) walk the stub and the
  private cross-link without ever loading verbatim content
  into forge artifacts.
- **Measurement source**: corpus-walk: WP-02a, WP-02b, WP-02c (Wiki PM observation counts per bucket); private full file at kurpatov-wiki-wiki/metadata/corpus-observations.md
- **Capability realised**: Develop wiki product line
  ([`../../capabilities/develop-wiki-product-line.md`](../../capabilities/develop-wiki-product-line.md))
  — Requirement traceability quality dimension + Architecture
  knowledge management.
- **Function**: Hold-corpus-observations-schema-public-side.
- **Element**: this file.
