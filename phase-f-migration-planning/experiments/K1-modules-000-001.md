# K1 — Wiki from scratch on modules 000 + 001

Active spec. Phase F migration-plan experiment that takes the
validated D8 pilot driver + Qwen3.6-27B-FP8 and runs it across
**all 44 sources of modules 000 and 001** of the
"Психолог-консультант" course on a fresh wiki branch — first end-
to-end production run beyond the canonical 7-source module-005
baseline.

This is **not a model-swap experiment** (G2/G3 falsified that
class). It is a *scale* experiment: how does the validated D8
pipeline behave at 6× the source count and across two modules
with non-trivial title overlap?

## Context

- v5 baseline: 7/7 sources of module 005 verified=ok in 169 min
  (~24 min/source). Tagged
  `canonical/qwen3.6-27b-fp8/module-005/2026-04-27` on
  `kurpatov-wiki-wiki`.
- Synth dedup test (this session): 2/2 sources verified=ok with
  the second source producing exactly the slim `## New ideas
  (verified)` section the time-saving goal requires. End-to-end
  pipeline (multi-format raw input + REPEATED detection +
  concept canonicalisation) confirmed working.
- Open Phase D sub-requirements (R-D-contract-prewrite,
  R-D-contract-xreflint, R-D-retrieval-cost) are *not* in scope
  for K1 — they are scheduled to land before any next model swap
  per the migration plan.

## Hypothesis (IF–THEN–BECAUSE)

> **IF** we run the validated D8 driver + Qwen3.6-27B-FP8 across
> all 3 sources of module 000 + all 41 sources of module 001
> (44 total), in source-order, on a fresh branch with empty
> `data/sources/` and `data/concepts/`,
>
> **THEN** at least 80 % of sources verify=ok, the cumulative
> wall ≤ 22 hours, REPEATED rate climbs as the index grows
> (because module 001 contains apparent title-duplicates and
> conceptual overlap with module 000), the concept catalogue ends
> at ≥ 30 distinct concepts, and the per-source structural-
> compliance violation rate stays ≤ 2/source on average.
>
> **BECAUSE** v5 measured 24 min/source on the same hardware,
> same model, same orchestrator. Title-duplicates within module
> 001 (`000 № 1. Вводная лекция`, `001 № 1. Вводная лекция`,
> `003 №2. Психодинамический подход`, `004 №2. …`, etc.) are
> exactly the case the synth dedup test validated. Stability over
> 22 h is the open question — this exercises the parked
> R-B-svcop-stable24h requirement empirically rather than
> hypothetically.

## Falsification criteria

K1 is *exploratory*; it cannot replace the next-three Phase F
experiments. It is falsified only on the broadest gates:

1. **Verify rate < 80 %.** More than 9 of 44 sources verify=fail.
   Indicates the orchestrator falls over at scale rather than on
   any single source — process gap.
2. **Wall > 30 hours.** Throughput degrades > 25 % vs the v5
   per-source rate, suggesting cumulative state growth (e.g.
   retrieval index size hurting embed_helpers) is biting.
3. **Stability event during the run** — the GPU UVM crash class
   (G1's Level-1 was 169 min sustained). A single crash is *data*
   for R-B-svcop-stable24h, not falsification. Two crashes is
   falsification (means G1's fix doesn't generalise to multi-
   module sustained runs).
4. **Cross-ref integrity violation rate > 5/source on average.**
   Same gate as G3 gate-4 — a wiki with broken `concepts_touched`
   slugs can't ship.

K1 success criteria are intentionally looser than G2/G3 because
those experiments tested *one-axis-at-a-time* component swaps
under known-good orchestration; K1 is the first time we exercise
the orchestration at scale.

## Sequenced work

1. **Patch driver.** Multi-module support (`D8_PILOT_MODULES`
   pipe-separated list); experiment-branch override; drop the
   index ≤ 6 cap; commit.
2. **Prepare workspace.** Clone wiki-raw + wiki-wiki. Branch
   `experiment/K1-2026-04-28-modules-000-001-qwen3.6-27b-fp8` off
   `skill-v2`. Clear `data/sources/`, `data/concepts/`,
   `data/embeddings/`. Commit empty state and push the K1 branch.
3. **Verify vLLM is on Qwen3.6-27B-FP8 + healthy.** Same model,
   same `.env`, same 400 W cap as v5.
4. **Launch K1 container** detached, named `d8-pilot-k1`, with:
   - `D8_PILOT_SKIP_CLONE=1` — workspace is pre-populated.
   - `D8_PILOT_COURSE=Психолог-консультант`.
   - `D8_PILOT_MODULES=000 Путеводитель по программе|001 Глубинная психология и психодиагностика в консультировании`.
   - `D8_PILOT_BRANCH=experiment/K1-2026-04-28-modules-000-001-qwen3.6-27b-fp8`.
5. **Monitor.** Periodic checks of `docker logs`, source.md and
   concept.md counts on the workspace, vLLM health endpoint, GPU
   thermals.
6. **Grade.** When complete, run `bench_grade.py` against the
   K1 wiki; record per-source claims/REPEATED/CF/violations,
   wall, REPEATED-rate-by-index, total concept count.
7. **Decide.** Promote K1 branch as a new canonical tag if all
   gates pass; otherwise capture lessons for the next iteration.

## Expected outcomes

If the hypothesis holds:

- 35-44 sources verified, ~16-22 h wall.
- REPEATED rate rises sharply once module 001 is hit (because
  there are visible title-duplicates inside module 001 — e.g.
  `000 № 1.` and `001 № 1.` are the same lecture from two angles).
- Concept catalogue grows from 0 to ~50-80 distinct concepts
  across the two modules.
- Per-source structural compliance comparable to v5 (≤ 1
  violation/source on average).
- Architect-velocity benefit: each subsequent module of similar
  size now has a known wall time, can be planned in calendar
  terms.

If falsified, the first signal is *which* gate triggered:

- Gate 1 (verify rate) → orchestration is not robust at scale;
  open H-* experiments before retry.
- Gate 2 (wall) → cumulative state growth; daemonize embed_helpers
  (R-D-retrieval-cost) before retry.
- Gate 3 (stability) → R-B-svcop-stable24h needs to land before
  any pilot crosses 8 h.
- Gate 4 (cross-ref) → R-D-contract-prewrite must land first.

## Cross-references

- Phase B capability targeted (indirectly): all four wiki
  capability
  [`../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md`](../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md).
- Phase D services exercised:
  [`llm-inference`](../../phase-d-technology-architecture/services/llm-inference.md),
  [`agent-orchestration`](../../phase-d-technology-architecture/services/agent-orchestration.md),
  [`vector-retrieval`](../../phase-d-technology-architecture/services/vector-retrieval.md).
- Synth predecessor (this session): the cognitive-dissonance
  dedup test under
  `/tmp/synth-K-test/wiki/data/sources/СинтТест/000 Дедуп-тест когнитивного диссонанса/`.
  Both sources verified; demonstrated REPEATED detection +
  slim "New ideas" section.
- Closed component-swap predecessors (different axis):
  [`G2-MoE-faster-inference.md`](G2-MoE-faster-inference.md),
  [`G3-gemma-4-31b.md`](G3-gemma-4-31b.md).
- Migration plan that orders K1 against the contract-enforcement
  experiments:
  [`../migration-plan.md`](../migration-plan.md).
- Pilot v5 baseline (the comparison target):
  `experiment/D8-pilot-2026-04-27-qwen3.6-27b-fp8` on
  `kurpatov-wiki-wiki`, tagged
  `canonical/qwen3.6-27b-fp8/module-005/2026-04-27`.


## Motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: K1 is the first end-to-end production run of
  the wiki-bench harness on real Kurpatov modules.
- **Goal**: TTS (reader time saved on modules 000+001).
- **Outcome**: 44 source.md + matching concept.md graph
  shipped on `kurpatov-wiki-wiki`.
- **Measurement source**: experiment-closure: K1 (44-source target; today 2 source.md shipped; verify rate per K1 spec gates)
- **Capability realised**: Develop wiki product line
  ([../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md](../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md)).
- **Function**: Compile-modules-000+001.
- **Element**: this file.
