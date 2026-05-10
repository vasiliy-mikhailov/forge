# Wiki product line

A family of forge products built on the same wiki-* labs and
the same forge capability ([`Develop wiki product line`](../capabilities/develop-wiki-product-line.md)),
differing only in which corpus they're applied to. Per-author
products on this line are owned by the **psi** subsidiary
(course-wiki); this file holds the line-wide product
decisions (membership shape, value proposition, line-wide
trajectories) and points to the daughter for per-author
detail.

## Members of the line

The members of this line are per-author wikis owned by the
psi subsidiary. Per [ADR 0030](../../phase-preliminary/adr/0030-subsidiary-url-visibility.md)
the subsidiary URL is permitted on forge-public; per-author
membership and per-author content (including which corpora
exist, status per author, quality numbers per release) lives
in the auth-gated daughter repo per
[ADR 0018](../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

Catalog entry: [`../subsidiaries/psi.md`](../subsidiaries/psi.md).

A new wiki product joins the line by:

1. New per-author content tree under `content/<author>/{raw,wiki}/`
   in the psi daughter repo (per the established per-author content tree shape).
2. Per-pilot env config (which raw tree, which wiki tree, which
   model) -- in the psi daughter.
3. Domain-specific fact-check sources and concept glossary in
   the psi daughter's `prompts/`.

No lab change. No capability extension. No new architecture on
the forge side.

## Why a line, not one product per author

The `wiki-*` labs (application components in
[`../../phase-c-information-systems-architecture/application-architecture/`](../../phase-c-information-systems-architecture/application-architecture/))
are content-agnostic. The lab structure does not change between
authors; only the input corpus, fact-check domain, and skill-v2
ritual's domain-specific glossary differ. Treating each author
as a fully separate product would duplicate the capability
description, the quality dimensions, and the trajectories. The
product line is the level at which those are stated once, on
the capabilities side.

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

- `R-B-voice-preservation` -- voice intact across all line
  members. First validation in flight on the inaugural psi
  product; second validation will follow on the second
  per-author wiki when it opens.
- `R-B-wiki-req-collection` -- every implementation choice on
  the line cites a requirement. Activity in
  [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
  walked at least once per product on the line.

Per-product trajectories (different status / different module
cadence) live in the psi daughter repo per author.

## Forward references

- [`../capabilities/develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)
  -- the capability the line draws on (operations, quality
  dimensions, realising labs).
- [`../subsidiaries/psi.md`](../subsidiaries/psi.md) -- the
  daughter that owns the per-author products on this line.
- [`../../phase-requirements-management/wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
  -- the wiki-PM activity that emits requirements for any
  product on this line.
- [`../../phase-c-information-systems-architecture/application-architecture/`](../../phase-c-information-systems-architecture/application-architecture/)
  -- the `wiki-*` labs that physically realise the capability.

## Measurable motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: forge runs multiple wiki products through the
  same labs; psi owns the per-author detail. The product-line
  file holds shared characteristics + the daughter pointer.
- **Goal**: TTS (KR: tts_share >= 0.30 per-use).
- **Outcome**: per-author wikis in the psi daughter cite back
  to this file's shared spec; this file cites back to the
  capability.
- **Measurement source**: experiment-closure data in psi
  per-product files; aggregated TTS KR is computed across
  per-author results.
- **Contribution**: product TTS share -- pending TTS harness
  (CI-1..7 cycle); when measured, per-source tts_share
  contributes to TTS KR rollup mean.
- **Capability realised**: Develop wiki product line
  ([../capabilities/develop-wiki-product-line.md](../capabilities/develop-wiki-product-line.md)).
- **Function**: Hold-shared-wiki-product-line-spec.
- **Element**: this file.
