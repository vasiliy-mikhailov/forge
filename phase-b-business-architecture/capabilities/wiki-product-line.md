# Wiki product-line capability stack

Applies to **Kurpatov Wiki** + **Tarasov Wiki** + future authors.

The same capability stack applies to every wiki product; differences
between products live in the input corpus + fact-check domain, not
in the lab structure. The `wiki-*` labs (application components in
Phase C) are content-agnostic — adding a new wiki product (e.g. for
a new author / corpus) requires only a new pair of
`<author>-wiki-{raw,wiki}` GitHub repos plus per-pilot env config;
no component change needed.

| Capability                           | Lab           | Quality dimension                                          |
|--------------------------------------|---------------|------------------------------------------------------------|
| Audio → text transcription           | wiki-ingest   | Russian-WER on a held-out audit set                        |
| Compile lecture into source.md       | wiki-bench    | **Fast for reading** — bullets, TL;DR, no narrative bloat  |
| Cross-source dedup of claims         | wiki-bench    | **No repetitions** — REPEATED markers, retrieval-augmented |
| Fact-check empirical claims          | wiki-bench    | **No fake statements** — Wikipedia URLs, CONTRADICTS_FACTS |
| Concept extraction + linking         | wiki-bench    | Canonical skill v2 shape                                   |
| Benchmark open-weight LLMs vs Opus   | wiki-bench    | Reproducible from `(Dockerfile + transcripts)` only        |
