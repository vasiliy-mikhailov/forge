# Tarasov Wiki

R&D output of forge. Smart-reading wiki distilled from audio/video
lectures by Vladimir Tarasov on management ("Управленческая борьба",
"Искусство управленческой борьбы", etc.). Same value stream and same capability
([`Develop wiki product line`](../capabilities/develop-wiki-product-line.md))
as Kurpatov Wiki, applied to management content
instead of psychology — and **preserves Тарасов's distinctive
voice** the same way Kurpatov Wiki preserves Курпатов's.

This product validates that the wiki-* labs are content-agnostic —
the same `wiki-ingest` / `wiki-compiler` / `wiki-bench`
infrastructure serves any audio-lecture corpus. It also validates
that voice-preservation generalises across authors with very
different rhetorical styles.

## Why this product (vs. a generic management summary)

Тарасов's value to the reader is not only the content of his
management theory — it is also *how he frames it*. His parables,
case studies from corporate practice, and didactic-aphoristic
delivery are part of what makes his lectures distinctive. A wiki
that strips the speaker's voice loses the differential value of
having compiled THIS author's work — exactly the same product-
line argument as for Kurpatov Wiki, see
[`../products/wiki-product-line.md`](../products/wiki-product-line.md)
for the full reasoning.

## Value stream

```
Tarasov audio/video lectures
    │ (collect)
    ▼  wiki-ingest lab — faster-whisper → raw.json
tarasov-wiki-raw repo (per-lecture whisper segments)
    │ (filter + adapt; preserve voice in narrative sections)
    ▼  wiki-bench lab — agent harness compiles + dedupes + factchecks
tarasov-wiki-wiki repo (per-source.md + per-concept.md, skill v2 shape)
    │
    ▼ (consume)
human reader — saves ~60 min per lecture per use,
              still hears Тарасов
```

## Member of

[`wiki-product-line.md`](wiki-product-line.md) — line membership and line-wide value proposition. The capability all line members exercise is [`Develop wiki product line`](../capabilities/develop-wiki-product-line.md).

## Capability drawn on

[`../capabilities/develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)
— same as Kurpatov Wiki; both products are members of the
[Wiki product line](wiki-product-line.md) and exercise the same
capability. Per-product differences live in input corpus,
fact-check domain (management literature for Tarasov), and
skill-v2 ritual's domain glossary — no capability extension.


## Source repos (planned)

- **`tarasov-wiki-raw`** — input, read-only for the bench. Format
  identical to `kurpatov-wiki-raw`: per-source whisper-segment
  `raw.json`. Populated by wiki-ingest.
- **`tarasov-wiki-wiki`** — output, with the same branch convention
  as the Kurpatov side (`main`, `skill-v2`, `bench/...`,
  `experiment/...`).

## Status

**Pre-pilot: content acquisition phase.** Kurpatov-Wiki was the
proof of concept for the wiki-* labs; Tarasov-Wiki is the
generalisation test. The labs themselves don't need any
methodology change — they're already content-agnostic. What's
needed:

1. Acquire Tarasov audio/video corpus.
2. Set up `tarasov-wiki-raw` GitHub repo + raw-pusher pointing at
   it.
3. Re-point wiki-ingest's whisper-watcher at the Tarasov vault.
4. Run a pilot (Tarasov module 0XX) through wiki-bench to validate
   that quality dimensions hold on management content
   (fact-check on management/business literature; concept
   extraction on negotiation/strategy terms; **voice preservation
   on Тарасов's parable/case-study delivery style**).

## Trajectories (Phase H)

| Capability | Level 1 (today) | Level 2 (next) | Metric delta |
|------------|-----------------|----------------|--------------|
| Audio → text transcription (Tarasov) | none | First Tarasov module transcribed | TBD |
| Compile lecture into source.md (Tarasov) | none | First pilot at Opus parity on a Tarasov module, voice preserved | TBD |

Per-capability detail will move into wiki-bench's
`STATE-OF-THE-LAB.md` once a Tarasov pilot launches.


## Measurable motivation chain
Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: Tarasov-wiki is the second-planned wiki product
  per [wiki-product-line.md](wiki-product-line.md); needs its
  forward-looking artifact.
- **Goal**: TTS (KR: tts_share ≥ 0.30 per-use).
- **Outcome**: when K1 closes for Kurpatov + Wiki PM walks
  Tarasov corpus, this file becomes the active product anchor.
- **Measurement source**: n/a — pending: Tarasov product not started; opens when Wiki PM walks Tarasov corpus per S1+S2
- **Contribution**: pending — product not started; opens when Wiki PM walks Tarasov corpus.
- **Capability realised**: Develop wiki product line.
- **Function**: Hold-Tarasov-wiki-forward-spec.
- **Element**: this file.
