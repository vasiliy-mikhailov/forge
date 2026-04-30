# Wiki product-line capability stack

The capabilities forge exercises to deliver every product on the
[Wiki product line](../products/wiki-product-line.md) (Kurpatov
Wiki + Tarasov Wiki + future authors). The line definition — which
products belong, why a line, line-wide value proposition — lives
on the products side; this file is the capabilities-angle view of
the same thing.

The stack is shared across line members because the `wiki-*` labs
(application components in
[`../../phase-c-information-systems-architecture/application-architecture/`](../../phase-c-information-systems-architecture/application-architecture/))
are content-agnostic. Per-product differences live in the input
corpus + fact-check domain + skill-v2 ritual's domain glossary,
not here.

## Capability stack

| Capability                           | Lab           | Quality dimension                                                                                |
|--------------------------------------|---------------|--------------------------------------------------------------------------------------------------|
| Wiki requirements collection         | (architect)   | **Every implementation choice cites a requirement** — prompts, schemas, graders reference R-IDs from `phase-requirements-management/catalog.md`; no orphan rules. Process: [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md). |
| Audio → text transcription           | wiki-ingest   | Russian-WER on a held-out audit set                                                              |
| Compile lecture into source.md       | wiki-bench    | **Fast for reading + preserves speaker voice** — bullets, TL;DR, no narrative bloat AND author's tone of voice intact in narrative sections (TL;DR + Лекция); structural sections stay neutral |
| Cross-source dedup of claims         | wiki-bench    | **No repetitions** — REPEATED markers, retrieval-augmented                                       |
| Fact-check empirical claims          | wiki-bench    | **No fake statements** — Wikipedia URLs, CONTRADICTS_FACTS                                       |
| Concept extraction + linking         | wiki-bench    | Canonical skill v2 shape                                                                         |
| Benchmark open-weight LLMs vs Opus   | wiki-bench    | Reproducible from `(Dockerfile + transcripts)` only                                              |

## Why "preserves speaker voice" is a binding capability dimension

Each wiki product the line serves is *valued because of WHO the
author is*, not just because of WHAT the author teaches. A reader
who reaches for Курпатов wants Курпатов's framing of psychology;
a reader who reaches for Тарасов wants Тарасов's framing of
management. Stripping the author's voice during compilation
collapses every product on the line into "generic <topic>
encyclopedia" — and that already exists; users don't need ours.

The compile-lecture-into-source.md capability therefore has TWO
quality dimensions, both binding:

- **Fast for reading.** Bullets, TL;DR, deduped claims,
  fact-checked citations, concept cross-links. Reader gets the
  gist in 1-2 minutes.
- **Preserves speaker voice.** Narrative sections (`## TL;DR`,
  `## Лекция (пересказ: только NEW и проверенное)`) keep the
  author's tone, characteristic phrasing, sceptical asides,
  metaphors. Structural sections (Claims, concepts) stay
  neutral and verifiable.

Failing on either dimension fails the capability. The skill-v2
contract enforces both via the per-source-summarize.md prompt's
Style section in each product's wiki repo (e.g.
`kurpatov-wiki-wiki:prompts/per-source-summarize.md`,
`tarasov-wiki-wiki:prompts/per-source-summarize.md`).

## Consumed by

- [`../products/wiki-product-line.md`](../products/wiki-product-line.md)
  — the product line that draws on this stack.
- [`../products/kurpatov-wiki.md`](../products/kurpatov-wiki.md),
  [`../products/tarasov-wiki.md`](../products/tarasov-wiki.md) —
  individual line members.

## Per-capability trajectories

Live in
[`../../phase-requirements-management/catalog.md`](../../phase-requirements-management/catalog.md)
as `R-B-...` rows (e.g. `R-B-voice-preservation`,
`R-B-wiki-req-collection`). When a row promotes to its Level 2,
the corresponding cell in the table above is updated and the row
is deleted from the catalog (per the trajectory model in
[`../../phase-preliminary/architecture-method.md`](../../phase-preliminary/architecture-method.md)).
