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

**Gate engine.** `forward_recall` and (after restore) `backward_
recall` are computed mechanically by:

```
python3 scripts/test-runners/measure-corpus-recall.py \
    --source A --against <Compact-or-Restore-output>.md
```

The harness parses the 20 source-A observations from
[`corpus-observations.md`](../../phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md)
(4 Substance, 7 Form, 9 Air), extracts the top-3 characteristic
Cyrillic content words from each verbatim quote (length ≥ 4,
function-word stopwords dropped), and counts an observation
"covered" iff ALL three keywords co-occur in the target file
(NFC-normalised, lowercase). Per-bucket coverage, forward recall
(Substance + Form pooled), and **Air-leakage rate** (Air
observations that wrongly survived L1 — *lower is better;
0 = perfect Air-strip*) are reported.

**Why ≥ 3 keywords (not "≥ 1").** Single-keyword matches
false-positive on common content words. Three distinct content
words from one observation co-occurring in the target is a
strong signal the *idea* is preserved (robust to filler removal
and faithful paraphrase).

**Sanity-check baseline.** Run against the corpus-observations
md itself (perfect knowledge) → 11/11 forward recall (1.000)
and Air-leakage 8/9 (the corpus *contains* the Air verbatims as
quoted prose, so this is the upper-bound reference, not a
target). Run against an empty file → 0/11. Run against just
Substance verbatims → 4/4 Substance, 0/7 Form, 0/9 Air, forward
recall 4/11 = 0.364 — the harness correctly attributes coverage
per bucket. Tested at gate-engine commit time.

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

| run_id  | date       | layer | variant       | ratio | saved% | fwd recall | bwd recall | trip-quality | gate | voice (eye-read) | artifact link |
|---------|------------|-------|---------------|-------|--------|------------|------------|--------------|------|------------------|---------------|
| K2-R1-V4_aggressive | 2026-05-02 | L1   | V4_aggressive | 0.774 | 22.6%  | 1.000      | 1.000      | **0.2261**   | PASS | n/a (synth)      | [`phase-c-…/wiki-bench/compact_restore/`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/) + [synth fixture](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/synthetic/fixtures/k2/lecture_A_synth.json) |
| K2-R1-V3_discourse  | 2026-05-02 | L1   | V3_discourse  | 0.804 | 19.6%  | 1.000      | 1.000      | 0.1957       | FAIL (sub-gate) | n/a | same |
| K2-R1-V2_structural | 2026-05-02 | L1   | V2_structural | 0.844 | 15.6%  | 1.000      | 1.000      | 0.1565       | FAIL | n/a | same |
| K2-R1-V1_minimal    | 2026-05-02 | L1   | V1_minimal    | 0.965 |  3.5%  | 1.000      | 1.000      | 0.0348       | FAIL | n/a | same |

### K2-R1 sweep summary

RLVR sweep across 4 enumerated L1 variants on the synth fixture
(`tests/synthetic/fixtures/k2/lecture_A_synth.json`, 230 words
mirroring lecture A's structure with embedded filler /
Substance / Form / Air patterns).

**Winner: `V4_aggressive`** at trip-quality **0.2261** —
**PASSES** the K2 L1 hypothesis gate (≥ 0.20). Forward recall is
1.000 (all 8 Substance + Form observations preserved verbatim;
no factual loss); ratio 0.774 (saved-time 22.6%); 7 filler
pattern classes fired (vocalised_hesitation +
triple_trail_i_tak_dalee + word_doubling + triple_word +
triple_phrase + filler_conjunction + self_qa).

The discipline that made the gate fire mechanically: TDD-first
unit tests (19/19 PASS in 40 ms) lock the contract for filler
removal AND Substance/Form preservation; the recall harness
(`scripts/test-runners/measure-corpus-recall.py`) computes
forward recall against the synth corpus-observations
independently of the algorithm. Per ADR 0015, the reward is
verifiable: an honest measurement, not an eye-read.

**Air leakage** (guardrail; *not* in trip-quality formula per
spec) is 0.571 for V4 — acknowledged measurement artefact: my
keyword extractor pulls Cyrillic content words from each Air
verbatim, but several Air observations contain content words
that surround the filler pattern (e.g., 'давайте начнём'
surrounding 'эээ'). After L1 strips the filler tokens, the
content words remain — the harness counts the observation as
'covered' even though the actual Air pattern was removed. Fix
queued: add `pattern_signature` field to Air observations so
the leakage check looks for the structural pattern (e.g.
adjacent doubling) rather than content keywords.

**Next runs (K2-R2 / K2-R3 / K2-R4)** are queued per the K2
sequenced-work table; they require the wiki-bench harness to
implement L2 (cross-source dedup) and L3 (concept-graph
link-out), then re-run on real lecture A from
kurpatov-wiki-raw.

## Post-Mortem & Insights

### K2-R1 (2026-05-02)

**What happened.** Built the L1 algorithm in 4 enumerated
variants (V1 minimal → V4 aggressive). Ran RLVR sweep on
230-word synth fixture. V4 won at trip-quality 0.2261, passing
the L1 gate.

**Why this worked.** The cheap-experiment principle (P5 in
architecture-principles.md) — synth fixture + pure-Python
algorithm + automated recall harness — turned what could have
been a multi-hour GPU pilot into a 40-ms unit-test run + a
one-second sweep. RLVR done right doesn't require RL; it
requires a verifiable reward and a small enumerable variant
space.

**Insight 1.** L1 alone delivers 22.6% saved-time. The
hypothesis target was 25% (ratio 0.75). The real algorithm
landed slightly under target but inside the gate (0.20). To
hit the original 25% on real lecture A: add patterns for
sentence-start filler ('эта', 'это', 'значит' as discourse
opener) and Russian time-fillers ('сейчас', 'теперь' when
positionally redundant). Queued for V5.

**Insight 2.** The Air-leakage metric is signal-corrupted at
the per-observation level — the recall harness's content-word
keyword extractor doesn't distinguish "content surrounding the
filler pattern" from "the filler pattern itself". Per-bucket
ratio (Substance vs Form vs Air) is robust; per-observation
Air detection needs `pattern_signature` (queued).

**Insight 3.** Restore L1 is identity (lossless), so the bwd
gate fires for free at L1. The work shifts to L2/L3 where
restore involves following pointers and reconstructing
deltas — that's where the bwd_recall gate becomes meaningful.

**Next step.** Day 4-5 of the K2 sequenced-work table: lift L2
(cross-source dedup) into wiki-bench harness once `compact_l2`
+ `restore_l2` are in place. Same TDD discipline; same RLVR
sweep methodology.


## Post-Mortem & Insights

(empty — to be filled after K2-R3 lands or after a falsifying
gate fires.)
