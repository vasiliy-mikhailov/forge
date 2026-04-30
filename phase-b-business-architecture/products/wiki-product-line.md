# Wiki product line

A family of forge products — **Kurpatov Wiki** + **Tarasov Wiki** +
future authors — built on the same shared capability stack and the
same wiki-* labs, differing only in which corpus they're applied
to. The product line is its own entry in this folder so that
shared product-level decisions (line membership, why a line, line-
wide value proposition) live alongside the per-product entries
they govern, instead of being buried inside the capability
description.

## Members of the line

| Product           | Status                                                            | Per-product detail                            |
|-------------------|-------------------------------------------------------------------|-----------------------------------------------|
| **Kurpatov Wiki** | Active — module 005 published as canonical Qwen3.6-27B-FP8 result | [`kurpatov-wiki.md`](kurpatov-wiki.md)        |
| **Tarasov Wiki**  | Pre-pilot — content acquisition phase                             | [`tarasov-wiki.md`](tarasov-wiki.md)          |
| Future authors    | None opened                                                       | (new pair of `<author>-wiki-{raw,wiki}` GitHub repos + per-pilot env config) |

## Why a line, not one product per author

The `wiki-*` labs (application components in
[`../../phase-c-information-systems-architecture/application-architecture/`](../../phase-c-information-systems-architecture/application-architecture/))
are content-agnostic. The lab structure does not change between
Kurpatov and Tarasov; only the input corpus, fact-check domain,
and skill-v2 ritual's domain-specific glossary differ. Treating
each author as a fully separate product would duplicate the
capability stack, the quality dimensions, and the trajectories.
The product line is the level at which those things are stated
once.

A new wiki product joins the line by:

1. New pair of `<author>-wiki-{raw,wiki}` GitHub repos
   (matching the `kurpatov-wiki-{raw,wiki}` shape).
2. Per-pilot env config (which raw repo, which wiki repo, which
   model).
3. Domain-specific fact-check sources and concept glossary in the
   wiki repo's `prompts/`.

No lab change. No new capability. No new architecture.

## Line-wide value proposition

Every product on this line answers the same reader question:

> *I want what THIS author teaches, in their voice, in 5-15
> minutes per lecture instead of 60-90, with the gist on top
> and verifiable structure underneath.*

The two parts of that question — **time saved** and **author's
voice intact** — are both binding. Either failure collapses the
product into "generic encyclopedia of <topic>", which already
exists and which users do not need ours for. The voice-preservation
constraint is what makes this line *the* place to wait for THIS
author's content, rather than to skim a Wikipedia article.

The compile-lecture-into-source.md capability therefore carries
two quality dimensions in the line's capability stack
([`../capabilities/wiki-product-line.md`](../capabilities/wiki-product-line.md)),
both binding:

- **Fast for reading.** Bullets, TL;DR, deduped claims,
  fact-checked citations, concept cross-links. Reader gets the
  gist in 1-2 minutes.
- **Preserves speaker voice.** Narrative sections (`## TL;DR`,
  `## Лекция (пересказ: только NEW и проверенное)`) keep the
  author's tone, characteristic phrasing, sceptical asides,
  metaphors. Structural sections (Claims, concepts) stay
  neutral and verifiable.

The voice-preservation constraint is enforced via the
per-source-summarize.md prompt's Style section in each product's
wiki repo (e.g. `kurpatov-wiki-wiki:prompts/per-source-summarize.md`,
`tarasov-wiki-wiki:prompts/per-source-summarize.md`).

## Capability stack

The capability rows that realise this product line live one folder
over, since they're "what forge can do" not "what forge ships":

→ [`../capabilities/wiki-product-line.md`](../capabilities/wiki-product-line.md)

Pinned highlight rows from that table (full table + quality
dimensions in the linked file):

- Wiki requirements collection
- Audio → text transcription
- Compile lecture into source.md
- Cross-source dedup of claims
- Fact-check empirical claims
- Concept extraction + linking
- Benchmark open-weight LLMs vs Opus

## Per-line trajectories

Per-line trajectories (Phase H) are the trajectory rows in the
[requirements catalog](../../phase-requirements-management/catalog.md)
whose Quality dim column starts with one of the line's capability
names. Today's open line-wide rows:

- `R-B-voice-preservation` — voice intact across all line members.
  Validated on K1 modules 000+001 (Kurpatov, in flight); future
  Tarasov pilot is the second validation.
- `R-B-wiki-req-collection` — every implementation choice on the
  line cites a requirement; activity in
  [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
  walked at least once per product on the line.

Per-product trajectories (different status / different module
cadence) live in the per-product files
([`kurpatov-wiki.md`](kurpatov-wiki.md),
[`tarasov-wiki.md`](tarasov-wiki.md)).

## Forward references

- [`../capabilities/wiki-product-line.md`](../capabilities/wiki-product-line.md)
  — the capability stack and quality dimensions this line draws on.
- [`kurpatov-wiki.md`](kurpatov-wiki.md), [`tarasov-wiki.md`](tarasov-wiki.md)
  — per-product detail.
- [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
  — the wiki-PM activity that emits requirements for any product
  on this line.
- [`../../phase-c-information-systems-architecture/application-architecture/`](../../phase-c-information-systems-architecture/application-architecture/)
  — the `wiki-*` labs that physically realise the capability stack.
