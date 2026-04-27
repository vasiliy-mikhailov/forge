# Kurpatov Wiki

R&D output of forge. Smart-reading wiki distilled from
~200 audio/video lectures by Andrey Kurpatov on psychology
("Системно-поведенческая психотерапия", "Психолог-консультант",
etc.). The wiki compresses ~60-90 min lectures into ~5-15 min
markdown articles with deduped claims, fact-checked attributions,
and concept cross-links.

## Value stream

```
Kurpatov audio/video lectures
    │ (collect)
    ▼  wiki-ingest lab — faster-whisper → raw.json
kurpatov-wiki-raw repo (per-lecture whisper segments)
    │ (filter + adapt)
    ▼  wiki-bench lab — agent harness compiles + dedupes + factchecks
kurpatov-wiki-wiki repo (per-source.md + per-concept.md, skill v2 shape)
    │
    ▼ (consume)
human reader — saves ~60 min per lecture per use
```

## Capabilities (from forge AGENTS.md Phase B)

| Capability                           | Lab          | Quality dimension                                          |
|--------------------------------------|--------------|------------------------------------------------------------|
| Audio → text transcription           | wiki-ingest  | Russian-WER on a held-out audit set                        |
| Compile lecture into source.md       | wiki-bench   | Fast for reading — bullets, TL;DR, no narrative bloat      |
| Cross-source dedup of claims         | wiki-bench   | No repetitions — REPEATED markers, retrieval-augmented     |
| Fact-check empirical claims          | wiki-bench   | No fake statements — Wikipedia URLs, CONTRADICTS_FACTS     |
| Concept extraction + linking         | wiki-bench   | Canonical skill v2 shape                                   |
| Benchmark open-weight LLMs vs Opus   | wiki-bench   | Reproducible from `(Dockerfile + transcripts)` only        |

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
- 199 lectures remain to be compiled.

## Trajectories (Phase H)

Per-capability trajectories live in
`phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/STATE-OF-THE-LAB.md`.
Headline next step: scale the same pilot driver to 200+ sources
without quality regression.
