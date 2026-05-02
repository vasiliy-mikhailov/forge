# Wiki product line

A family of forge products — **Kurpatov Wiki** + **Tarasov Wiki** +
future authors — built on the same wiki-* labs and the same
forge capability ([`Develop wiki product line`](../capabilities/develop-wiki-product-line.md)),
differing only in which corpus they're applied to. The product
line is its own entry in this folder so that line-wide product
decisions (membership, value proposition, line-wide trajectories)
live alongside the per-product entries they govern.

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
capability description, the quality dimensions, and the
trajectories. The product line is the level at which those are
stated once, on the capabilities side.

A new wiki product joins the line by:

1. New pair of `<author>-wiki-{raw,wiki}` GitHub repos
   (matching the `kurpatov-wiki-{raw,wiki}` shape).
2. Per-pilot env config (which raw repo, which wiki repo, which
   model).
3. Domain-specific fact-check sources and concept glossary in the
   wiki repo's `prompts/`.

No lab change. No capability extension. No new architecture.

## Line-wide value proposition

Every product on this line answers the same reader question:

> *I want what THIS author teaches, in their voice, in 5-15
> minutes per lecture instead of 60-90, with the gist on top
> and verifiable structure underneath.*

Both halves of that question are binding. Either failure
collapses the product into "generic encyclopedia of <topic>",
which already exists and which users do not need ours for. The
voice-preservation constraint is what makes this line *the*
place to wait for THIS author's content, rather than to skim a
Wikipedia article. It's a quality dimension of the
[`Develop wiki product line`](../capabilities/develop-wiki-product-line.md)
capability, not just a tagline.

## Capability the line draws on

→ [`../capabilities/develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)

That file holds the Capability Map (Transcription,
Compilation, LLM serving, Wiki requirements collection), each
operation's quality dimensions, the labs that realise it, the
sub-trajectories rolled into Phase D, and the references to the
forge-level capabilities (R&D, Product delivery, Architecture
knowledge management) it decomposes.

## Per-line trajectories

Per-line trajectories (Phase H) are the trajectory rows in the
[requirements catalog](../../phase-requirements-management/catalog.md)
whose Quality dim column starts with one of the line's quality
dimensions. Today's open line-wide rows:

- `R-B-voice-preservation` — voice intact across all line
  members. Validated on K1 modules 000+001 (Kurpatov, in
  flight); future Tarasov pilot is the second validation.
- `R-B-wiki-req-collection` — every implementation choice on the
  line cites a requirement. Activity in
  [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
  walked at least once per product on the line.

Per-product trajectories (different status / different module
cadence) live in the per-product files
([`kurpatov-wiki.md`](kurpatov-wiki.md),
[`tarasov-wiki.md`](tarasov-wiki.md)).

## Forward references

- [`../capabilities/develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)
  — the capability the line draws on (operations, quality
  dimensions, realising labs).
- [`kurpatov-wiki.md`](kurpatov-wiki.md), [`tarasov-wiki.md`](tarasov-wiki.md)
  — per-product detail.
- [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
  — the wiki-PM activity that emits requirements for any product
  on this line.
- [`../../phase-c-information-systems-architecture/application-architecture/`](../../phase-c-information-systems-architecture/application-architecture/)
  — the `wiki-*` labs that physically realise the capability.


## Motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: forge ships multiple wiki products (Kurpatov,
  Tarasov, future). The product-line file holds shared
  characteristics + per-wiki branches.
- **Goal**: TTS (reader time saved per use) + PTS (cumulative
  across users).
- **Outcome**: per-wiki product folders under
  [products/](.) cite back to this file's shared spec.
- **Capability realised**: Develop wiki product line
  ([../capabilities/develop-wiki-product-line.md](../capabilities/develop-wiki-product-line.md)).
- **Function**: Hold-shared-wiki-product-line-spec.
- **Element**: this file.
