# K2 — Two-way compact / restore on Kurpatov lecture A

Active spec. Phase F R&D experiment driven by the
[Wiki PM role](../../phase-b-business-architecture/roles/wiki-pm.md)
on behalf of the
[Develop wiki product line](../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md)
capability — quality dimensions **Reading speed** (forward) and
**Concept-graph quality** + **Voice preservation** (backward).

K-prefix: Kurpatov-wiki R&D, sequenced after K1 (modules 000+001
end-to-end compilation). Where K1 measured *can the pipeline
ship a wiki*, K2 measures *can the wiki be losslessly compacted
and restored* — i.e. once a wiki exists, can the reader spend a
fraction of the original lecture's tokens to acquire the same
idea-pool, and can the lecture be reconstructed from the compact
form when the architect needs to verify provenance.

## Context

- The Wiki PM role's S1+S2 corpus walk
  ([`phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md`](../../phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md))
  classified observations into three buckets:
  - **Substance** — claims, definitions, attributions (the
    information).
  - **Form** — voice signature: branded methods, scenario
    framing, synonym chains, direct address (the *how* the
    information is delivered; lossy to drop).
  - **Air** — filler patterns: triple-trail "и так далее",
    spoken-word-doubling, self-Q&A scaffolding (no information
    beyond the surrounding Substance / Form).
- Source A in that corpus is module 000 / lecture
  `000 Знакомство с программой «Психолог-консультант»`
  (~9 963 words, 88-min spoken; raw at
  `kurpatov-wiki-raw/data/Психолог-консультант/000 Путеводитель по программе/000 Знакомство с программой «Психолог-консультант»/raw.json`).
- Source B is the human-written конспект of the same lecture
  (3 391 words; A→B compression ratio = **0.34**). Already-edited
  synopsis. The human conспект is the *de-facto baseline* for
  "what a reader is willing to accept as a compact form" — K2's
  algorithmic compaction must beat or match this ratio without
  losing recall against A.

## Hypothesis (IF–THEN–BECAUSE)

> **IF** we apply layered compaction to lecture A —
>
> - **L1 Air-strip**: drop tokens classified as Air (filler,
>   triple-trail и-так-далее, spoken doubling, self-Q&A
>   scaffolding) per the Wiki PM bucket spec.
> - **L2 Cross-source idea dedup**: detect ideas / stories
>   already published in earlier wiki sources (`data/sources/`
>   on `kurpatov-wiki-wiki`) and replace with a one-sentence
>   pointer + delta of new details only.
> - **L3 Concept-graph link-out**: replace expansive definitions
>   of concepts already in `data/concepts/` with concept-link
>   stubs (`[concept](../concepts/<slug>.md)`); keep only the
>   delta-detail.
>
> **THEN**:
>
> 1. Forward direction (compact). Compact(A) preserves ≥ **0.90**
>    of A's idea pool (recall against the human-tagged Substance
>    + Form observations in corpus-observations.md) at compression
>    ratio ≤ **0.40** (token-count compact / original;
>    competitive with the human конспект's 0.34).
> 2. Backward direction (restore). Restore(Compact(A)) reconstructs
>    A's idea pool with recall ≥ **0.95** (the missing ≤ 5% is
>    Air; restoring Air *verbatim* is not a goal — only the
>    information the lecture conveyed). Restoration is performed
>    by an LLM-with-tool-access agent that follows compact-form
>    pointers back to `data/sources/` and `data/concepts/` to
>    re-expand the deltas.
> 3. Saved-time%. Reader-perceived saved time is approximated by
>    `1 - tok(Compact(A)) / tok(A)` ≥ **60%** at L1+L2+L3 layered.
>    L1 alone target ≥ 25%; L1+L2 ≥ 45%; L1+L2+L3 ≥ 60%.
>
> **BECAUSE**: the corpus walk already empirically separated Air
> (≈ pattern P1+P2+P3 in WP-07/08/09; 8 / 13 substantive
> observations were Air-class for source A). Cross-source dedup
> is not theoretical — wiki-bench's REPEATED detection (validated
> in K1 synth tests) is the same machinery, applied at compaction
> time instead of compilation time. Concept-graph link-out is
> already the wiki-compiler's `concepts_touched` mechanism in
> reverse: instead of *consuming* a concept link from a source
> being written, *emit* a concept link from a source being read.

## Falsification criteria

K2 is *exploratory* like K1; the broadest gates falsify only the
methodology, not the wiki itself.

1. **Forward recall < 0.85.** Compact(A) loses more than 15% of
   A's tagged idea pool. Air-strip is over-aggressive OR
   Substance/Form are leaking into Air. Gate: re-walk the bucket
   classifier; if WP-07..14 have regressed, fix the classifier
   first.
2. **Backward recall < 0.85 from Compact(A).** Restore(Compact(A))
   loses substance even after the agent follows pointers. Means
   the cross-source / concept-graph deltas don't carry enough
   info to reconstruct the original chain. Gate: increase L2 / L3
   delta verbosity (smaller saved%, higher recall — lemma trade-
   off).
3. **Compression ratio > 0.55.** Algorithmic compact is worse
   than naive Air-strip at L1 (compress should be 0.55..0.75
   from L1 alone). Means L2 / L3 are net-negative — the deltas +
   pointers cost more tokens than they save.
4. **Voice preservation regression.** Human eye-read of Compact(A)
   reports the lecture no longer sounds like Курпатов (Voice
   preservation Form-bucket leakage into Air). Falsifies the
   "Air doesn't include Form" axis of the bucket spec.

K2 success at L1+L2+L3 = a 6× reading-speed improvement over the
raw lecture with measurable provenance; both directions
verifiable without architect eye-read.

## Parameters

### Fixed

- **Single source under test**: lecture A (module 000 / 000
  Знакомство; 9 963 words, single ~10K block, no segment-level
  paragraph breaks — see `corpus-observations.md` row A).
- **Tokenizer for ratio measurement**: `tiktoken` cl100k\_base
  (used elsewhere in forge for vLLM context budgeting). Fix the
  tokenizer so ratios are comparable across runs.
- **Compact-form schema** (frontmatter + sections — fences
  unindented so the link checker doesn't mistake the example's
  bracketed text for live links):

```
---
source: <stem>
course: Психолог-консультант
module: 000 Путеводитель
ratio: 0.NN
pointers: [<source-stem-1>, <source-stem-2>, …]
concepts: [<slug-1>, <slug-2>, …]
---
## TL;DR
…
## Substance
…
## Form (voice signature)
…
## Cross-references (delta only)
- [Idea X — full at](sources/<stem>.md): … delta detail …
- [Concept Y](../concepts/<slug>.md): … delta detail …
```

- **Restoration agent**: same OpenHands SDK harness as K1
  (`forge-kurpatov-wiki:latest` + Qwen3.6-27B-FP8 vLLM serving).
  No model swap.

### Variables (DoE matrix)

| Run | Layer set         | Filler list                | Dedup model        | Δ-cap |
|-----|-------------------|----------------------------|--------------------|-------|
| K2-R1 | L1 only         | Wiki-PM corpus-obs filler  | n/a                | n/a   |
| K2-R2 | L1 + L2         | same                       | wiki-bench REPEATED  | 30 tok / pointer |
| K2-R3 | L1 + L2 + L3    | same                       | + concept-link-out | 50 tok / link    |
| K2-R4 | L1 + L2 + L3    | extended (architect-curated) | as R3            | as R3            |

### Variables held under R-NN trajectories

- **R-B-voice-preservation** — open. Voice preservation is part
  of the K2 success criterion; if it lifts as a side-effect of
  L1/L2/L3 doing the right thing, log on the R-NN closure track.
- **R-B-wiki-req-collection** — closed at L2 (per audit history).
  K2 is one of the activities that exercises the closed L2.

## Evaluation

### Primary metric

**Trip-quality** = `min(forward_recall, backward_recall) ×
(1 - compression_ratio)`. Range 0..1. Higher = better.

| Variant | Hypothesis target |
|---------|-------------------|
| L1 only      | ≥ 0.20 (recall ~0.95, ratio ~0.75 → 0.95 × 0.25 = 0.24)  |
| L1 + L2      | ≥ 0.40 (recall ~0.92, ratio ~0.55 → 0.92 × 0.45 = 0.41)  |
| L1 + L2 + L3 | ≥ 0.50 (recall ~0.90, ratio ~0.40 → 0.90 × 0.60 = 0.54)  |

### Guardrail metrics

- **No factual loss.** Restore(Compact(A)) preserves every
  attributable claim in A (Selye / стресс, Сократ, the founding
  examples). Mechanical check: every claim with explicit
  attribution in Substance must round-trip verbatim or with
  paraphrase that preserves the attribution.
- **No fabrication.** Restore(Compact(A)) introduces no claim
  not present in A or in the cross-referenced sources / concepts
  the compact-form pointed to. Mechanical: cross-check restored
  claims against the source-pool union (A ∪ pointers ∪ concepts).
- **Concept-graph integrity.** Every concept link emitted by L3
  resolves to an existing `data/concepts/<slug>.md`. Same gate
  as the wiki-compiler's existing `concepts_touched` integrity
  check.

### Test set

K2-R1..R3: lecture A only (single source, 9 963 words).
K2-R4: lecture A + lectures C, D (module 005 sources, denser
content per the corpus-observations dimensions table) — proves
the algorithm generalises beyond the pilot source.

## Sequenced work

1. **Day 0 — Wiki PM** authors this spec, the catalog row
   `R-B-compact-restore`, and the wiki-bench backlog entry K2.
2. **Day 1 — wiki-bench harness** implements `compact()` as a
   skill v2 variant (the L1 Air-strip is mechanical; L2/L3 use
   the existing REPEATED + concepts_touched machinery against
   the live `kurpatov-wiki-wiki` repo).
3. **Day 2 — wiki-bench harness** implements `restore()` as a
   skill (LLM-with-tool-access agent following pointers).
4. **Day 3 — first run K2-R1** (L1 only). Measure ratio, recall,
   trip-quality. Architect eye-read for Voice preservation.
5. **Day 4-5 — K2-R2 (L1+L2) and K2-R3 (L1+L2+L3)**.
6. **Day 6 — K2-R4** (multi-source generalisation). Pivot or
   scale based on the trip-quality table.
7. **Promote** to a Phase H trajectory closure: lift `R-B-compact-
   restore` from Level 1 (no algorithm) to Level 2 (algorithm
   shipped, trip-quality ≥ 0.50 measured on lecture A).

## Team

| Function                          | Today                                                                                                  |
|-----------------------------------|--------------------------------------------------------------------------------------------------------|
| **Wiki PM** (this spec; acceptance) | The role itself — authors spec, the catalog row, falsification gates, eye-read voice preservation.    |
| **Developer** (compact + restore implementation) | OpenHands SDK agent in [`wiki-bench`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/) running [`SKILL.md`](https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/tree/main/skills/benchmark) — the same harness K1 used. |
| **DevOps** (data + harness)       | Not invoked today. Lecture A's raw.json already lands on `kurpatov-wiki-raw` via the validated wiki-ingest pipeline (ADR 0005). No new infra; no service rollout. The wiki-bench Make targets already wire `compact()` and `restore()` as skill variants. |

The Wiki PM does *not* implement compact() or restore(). The
agent in wiki-bench implements them. The Wiki PM authors the
hypothesis, the falsification gates, the metrics; reviews the
output; eye-reads voice preservation; emits the closure ADR if
the trajectory lifts.

## Execution log

| run\_id | date | layer | ratio | fwd recall | bwd recall | trip-quality | voice (eye-read) | artifact link |
|---------|------|-------|-------|------------|------------|--------------|------------------|---------------|
| (none yet — Day 0) | | | | | | | | |

## Post-Mortem & Insights

(empty — to be filled after K2-R3 lands or after a falsifying
gate fires.)
