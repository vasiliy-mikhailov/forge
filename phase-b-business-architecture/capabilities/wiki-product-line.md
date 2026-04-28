# Wiki product-line capability stack

Applies to **Kurpatov Wiki** + **Tarasov Wiki** + future authors.

The same capability stack applies to every wiki product; differences
between products live in the input corpus + fact-check domain, not
in the lab structure. The `wiki-*` labs (application components in
Phase C) are content-agnostic — adding a new wiki product (e.g. for
a new author / corpus) requires only a new pair of
`<author>-wiki-{raw,wiki}` GitHub repos plus per-pilot env config;
no component change needed.

| Capability                           | Lab           | Quality dimension                                                                                |
|--------------------------------------|---------------|--------------------------------------------------------------------------------------------------|
| Audio → text transcription           | wiki-ingest   | Russian-WER on a held-out audit set                                                              |
| Compile lecture into source.md       | wiki-bench    | **Fast for reading + preserves speaker voice** — bullets, TL;DR, no narrative bloat AND author's tone of voice intact in narrative sections (TL;DR + Лекция); structural sections stay neutral |
| Cross-source dedup of claims         | wiki-bench    | **No repetitions** — REPEATED markers, retrieval-augmented                                       |
| Fact-check empirical claims          | wiki-bench    | **No fake statements** — Wikipedia URLs, CONTRADICTS_FACTS                                       |
| Concept extraction + linking         | wiki-bench    | Canonical skill v2 shape                                                                         |
| Benchmark open-weight LLMs vs Opus   | wiki-bench    | Reproducible from `(Dockerfile + transcripts)` only                                              |

## Why "preserves speaker voice" is a product-line requirement

Each wiki product the line serves is *valued because of WHO the
author is*, not just because of WHAT the author teaches. A reader
who reaches for Курпатов wants Курпатов's framing of psychology;
a reader who reaches for Тарасов wants Тарасов's framing of
management. Stripping the author's voice during compilation
collapses every product on the line into "generic <topic>
encyclopedia" — and that already exists; users don't need ours.

The compile-lecture-into-source.md capability therefore has TWO
quality dimensions, both binding:

- **Fast for reading.** Bullets, TL;DR, deduped claims, factchecked
  citations, concept cross-links. A reader gets the gist in
  1-2 minutes.
- **Preserves speaker voice.** Narrative sections (`## TL;DR`,
  `## Лекция (пересказ: только NEW и проверенное)`) keep the
  author's tone, characteristic phrasing, sceptical asides,
  metaphors. Structural sections (Claims, concepts) stay
  neutral and verifiable.

Failing on either dimension fails the capability. The skill-v2
contract enforces both via the per-source-summarize.md prompt's
Style section in each product's wiki repo (e.g.
`kurpatov-wiki-wiki:prompts/per-source-summarize.md`).
