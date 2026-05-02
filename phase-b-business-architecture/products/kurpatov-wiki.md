# Kurpatov Wiki

R&D output of forge. Smart-reading wiki distilled from
~200 audio/video lectures by Andrey Kurpatov on psychology
("Системно-поведенческая психотерапия", "Психолог-консультант",
etc.). The wiki compresses ~60-90 min lectures into ~5-15 min
markdown articles with deduped claims, fact-checked attributions,
concept cross-links **— and preserves Курпатов's distinctive voice**.

## Why this product (vs. a generic encyclopedia summary)

Курпатов's value to the reader is not only the content of his
psychology — it is also *how he frames it*. His charisma, sceptical
asides, characteristic metaphors, and aphoristic turns are part of
what makes someone reach for his lectures rather than for a
neutral textbook. A wiki that strips out the speaker's voice
loses the differential value of having compiled THIS author's
work.

The product therefore has a hard requirement: **narrative sections
of every source.md preserve the speaker's tone of voice and
performer's style**. Where Курпатов is sceptical, the prose is
sceptical. Where he uses a vivid metaphor, the metaphor is kept
(quoted or near-quoted, not paraphrased into neutrality). Where
he addresses the listener directly ("посмотрите", "представьте"),
the address survives.

This is balanced against the equally hard "save reader time" goal
by splitting the sections of source.md into two registers:

- **Narrative sections** (`## TL;DR`, `## Лекция (пересказ: только NEW и проверенное)`)
  — preserve voice. These are what a fast reader skims.
- **Structural sections** (`## Claims — provenance and fact-check`,
  `## New ideas (verified)`, `## All ideas`, concept articles)
  — neutral and structural. These are what a careful reader
  cross-references.

The split lets a reader who wants the gist skim the narrative
sections in 1-2 minutes and still hear Курпатов; while a reader
who wants verifiability drops into the Claims block and gets
neutral fact-checked statements.

The skill-v2 contract enforcement is in
`kurpatov-wiki-wiki:prompts/per-source-summarize.md` § Style; the
runtime injection is in
[`../../phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator/run-d8-pilot.py`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator/run-d8-pilot.py)
SOURCE_AUTHOR_PROMPT § "Tone of voice".

## Value stream

```
Kurpatov audio/video lectures
    │ (collect)
    ▼  wiki-ingest lab — faster-whisper → raw.json
kurpatov-wiki-raw repo (per-lecture whisper segments)
    │ (filter + adapt; preserve voice in narrative sections)
    ▼  wiki-bench lab — agent harness compiles + dedupes + factchecks
kurpatov-wiki-wiki repo (per-source.md + per-concept.md, skill v2 shape)
    │
    ▼ (consume)
human reader — saves ~60 min per lecture per use,
              still hears Курпатов
```

## Member of

[`wiki-product-line.md`](wiki-product-line.md) — line membership and line-wide value proposition. The capability all line members exercise is [`Develop wiki product line`](../capabilities/develop-wiki-product-line.md).

## Capability drawn on

[`../capabilities/develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)
— the same capability all line members exercise. Operations
stack (Transcription / Compilation / LLM serving / Wiki
requirements collection), per-operation quality dimensions, and
realising labs are described once there.


## Source repos

- **`kurpatov-wiki-raw`** — input. Read-only for the bench. Contains
  `data/<course>/<module>/<source>/raw.json` (whisper segments).
  Populated by wiki-ingest lab.
- **`kurpatov-wiki-wiki`** — output. Branches:
  - `main` — production state (Mac-side Cowork users).
  - `skill-v2` — the 12-step ritual; canonical experiment branch
    target.
  - `bench/<date>-<served>` — baseline runs.
  - `experiment/<exp-id>-<date>-<served>` — labelled experiments.

## Status

- Module 005 of "Психолог-консультант" published as canonical
  Qwen3.6-27B-FP8 compilation, tagged
  `canonical/qwen3.6-27b-fp8/module-005/2026-04-27` on `skill-v2`
  (merge commit 3fd8b18).
- K1 experiment in flight: modules 000 + 001 from scratch
  (44 sources). See
  [`../../phase-f-migration-planning/experiments/K1-modules-000-001.md`](../../phase-f-migration-planning/experiments/K1-modules-000-001.md).
- 199 lectures remain to be compiled.

## Trajectories (Phase H)

Per-capability trajectories live in
[`../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/STATE-OF-THE-LAB.md`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/STATE-OF-THE-LAB.md).
Headline next step: scale the same pilot driver to 200+ sources
without quality regression — including without voice regression.


## Measurable motivation chain
Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: Kurpatov-wiki is the first product on the wiki
  product line; needs its product-page artifact.
- **Goal**: TTS (KR: tts_share ≥ 0.30 per-use).
- **Outcome**: K1 modules 000+001 + K2 compact-restore both
  cite this product's R-NN trajectories.
- **Measurement source**: experiment-closure: K1 + K2 (per kurpatov-wiki-wiki source.md / concept.md counts + K2 trip-quality on real lecture A)
- **Contribution**: product TTS share — pending TTS harness (CI-1..7 cycle); when measured, per-source tts_share contributes to TTS KR rollup mean. K1 v2 published 44 sources at 71min wall; per-reader savings TBD.
- **Capability realised**: Develop wiki product line.
- **Function**: Anchor-Kurpatov-wiki-product-content.
- **Element**: this file.
