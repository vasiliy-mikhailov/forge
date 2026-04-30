# Wiki product line

A family of forge products — **Kurpatov Wiki** + **Tarasov Wiki** +
future authors — built on the same wiki-* labs and the same set of
operations, differing only in which corpus they're applied to.

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
operations stack, the quality dimensions, and the trajectories.
The product line is the level at which those are stated once.

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

Both halves of that question are binding. Either failure collapses
the product into "generic encyclopedia of <topic>", which already
exists and which users do not need ours for. The voice-preservation
constraint is what makes this line *the* place to wait for THIS
author's content, rather than to skim a Wikipedia article.

## Operations the line performs (and which forge capability each draws on)

These are the line's operational steps — what wiki-* labs *do* to
turn a corpus into a published wiki. Each step is a use of one of
forge's four real Phase B capabilities (see
[`../capabilities/forge-level.md`](../capabilities/forge-level.md)):
**R&D**, **Service operation**, **Product delivery**, **Architecture
knowledge management**. Per-step quality dimensions are what the
line is judged on.

| Operation                            | Lab           | Forge capability drawn on               | Quality dimension                                                                                |
|--------------------------------------|---------------|------------------------------------------|--------------------------------------------------------------------------------------------------|
| Wiki requirements collection         | (architect)   | Architecture knowledge management        | **Every implementation choice cites a requirement** — prompts, schemas, graders reference R-IDs from `phase-requirements-management/catalog.md`; no orphan rules. Process: [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md). |
| Audio → text transcription           | wiki-ingest   | Service operation                        | Russian-WER on a held-out audit set                                                              |
| Compile lecture into source.md       | wiki-bench    | R&D + Product delivery                   | **Fast for reading + preserves speaker voice** — bullets, TL;DR, no narrative bloat AND author's tone of voice intact in narrative sections (TL;DR + Лекция); structural sections stay neutral |
| Cross-source dedup of claims         | wiki-bench    | R&D                                      | **No repetitions** — REPEATED markers, retrieval-augmented                                       |
| Fact-check empirical claims          | wiki-bench    | R&D                                      | **No fake statements** — Wikipedia URLs, CONTRADICTS_FACTS                                       |
| Concept extraction + linking         | wiki-bench    | R&D                                      | Canonical skill v2 shape                                                                         |
| Benchmark open-weight LLMs vs Opus   | wiki-bench    | R&D                                      | Reproducible from `(Dockerfile + transcripts)` only                                              |

This table sits on the products side because each row describes
*what this product line does*, not *what forge can do in the
abstract*. The forge-level capabilities are the abstract abilities;
the operations above are the concrete steps the wiki-* labs run to
exercise those abilities for this specific product line.

## Why "preserves speaker voice" is binding

Each wiki product the line serves is *valued because of WHO the
author is*, not just because of WHAT the author teaches. A reader
who reaches for Курпатов wants Курпатов's framing of psychology;
a reader who reaches for Тарасов wants Тарасов's framing of
management. Stripping the author's voice during compilation
collapses every product on the line into "generic <topic>
encyclopedia."

The Compile-lecture-into-source.md operation therefore has TWO
quality dimensions, both binding:

- **Fast for reading.** Bullets, TL;DR, deduped claims,
  fact-checked citations, concept cross-links. Reader gets the
  gist in 1-2 minutes.
- **Preserves speaker voice.** Narrative sections (`## TL;DR`,
  `## Лекция (пересказ: только NEW и проверенное)`) keep the
  author's tone, characteristic phrasing, sceptical asides,
  metaphors. Structural sections (Claims, concepts) stay
  neutral and verifiable.

Failing on either dimension fails the operation. The skill-v2
contract enforces both via the per-source-summarize.md prompt's
Style section in each product's wiki repo (e.g.
`kurpatov-wiki-wiki:prompts/per-source-summarize.md`,
`tarasov-wiki-wiki:prompts/per-source-summarize.md`).

## Per-line trajectories

Per-line trajectories (Phase H) are the trajectory rows in the
[requirements catalog](../../phase-requirements-management/catalog.md)
whose Quality dim column starts with one of the line's operation
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

- [`../capabilities/forge-level.md`](../capabilities/forge-level.md)
  — the four real Phase B capabilities every operation above
  draws on.
- [`kurpatov-wiki.md`](kurpatov-wiki.md), [`tarasov-wiki.md`](tarasov-wiki.md)
  — per-product detail.
- [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
  — the wiki-PM activity that emits requirements for any product
  on this line.
- [`../../phase-c-information-systems-architecture/application-architecture/`](../../phase-c-information-systems-architecture/application-architecture/)
  — the `wiki-*` labs that physically realise the operations stack.
