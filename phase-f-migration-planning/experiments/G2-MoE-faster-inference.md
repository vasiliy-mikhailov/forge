# G2 — Faster inference via MoE (swap to Qwen3.6-35B-A3B)

Active spec. Phase F — Migration Planning experiment that sequences
the work to swap the LLM component behind the LLM-inference
technology service (Phase D), in order to advance the *throughput*
quality dimension of the Service Operation capability (Phase B).

This is a Phase F doc — Phase B's capability stays the same;
Phase D's tech service stays the same; only the *component
realising* the service changes.

## Context

Pilot v5 (2026-04-27) measured Qwen3.6-27B-FP8 dense decode at
~47 tok/s batch=1 on the RTX PRO 6000 Blackwell at 400 W cap. That's
~80 % of the theoretical memory-bandwidth ceiling for a dense FP8
27 B model on this card (≈ 1.6 TB/s HBM ÷ 27 GB weights ≈ 60 tok/s).
Pilot wall on module 005 was 169 min for 7 sources.

Decode is the bottleneck (pilot wall is decode-bound; prefill takes
~30 % of LLM wall). To raise the ceiling, the binding lever is the
*per-token bytes-read* number — which a Mixture-of-Experts model
reduces directly.

## Hypothesis (IF–THEN–BECAUSE)

> **IF** we swap the served model from Qwen3.6-27B-FP8 (dense, all
> 27 B params active per decode step) to Qwen3.6-35B-A3B (Mixture-of-
> Experts: 35 B total params, only ~3 B active per token via expert
> routing), keeping the Blackwell, the 400 W power cap, the
> persistence-mode unit, vLLM 0.19.1, and the rest of the stack
> unchanged,
>
> **THEN** decode throughput on the Blackwell will rise ~4-8×
> (target ≥ 100 tok/s, plausibly 200+), pilot wall on a 7-source
> module will drop from ~169 min to ~50-90 min, and quality on the
> wiki-compilation task will hold within ±20 % of the dense-27 B
> baseline measured by `bench_grade.py --compare-with` (claims_total,
> claims_REPEATED, claims_CONTRADICTS_FACTS, concepts_count,
> all_violations).
>
> **BECAUSE** decode on a single Blackwell is memory-bandwidth-bound
> (47 tok/s ≈ 80 % of the dense-27B ceiling). MoE inference reads
> only the active experts per token (~3 GB per step at FP8 instead
> of ~27 GB), raising the ceiling roughly an order of magnitude.
> The 35 B total params fit in 97 GB VRAM with headroom for KV cache
> and activations. Quality is hypothesised at-or-near 27 B dense per
> the Qwen team's published benchmarks, but the wiki-compilation
> domain is not on those benchmarks — that's what the experiment
> validates.

## Falsification criteria

Run a full pilot v6 against module 005 with Qwen3.6-35B-A3B and
compare to pilot v5's published metrics. Falsify if **either**:

1. **Throughput floor not reached.** Decode throughput < 80 tok/s
   batch=1 on the Blackwell at 400 W cap. MoE benefit didn't
   materialise on this hardware in this vLLM version.
2. **Quality regression > 20 %.** Any of these vs pilot v5 baseline
   (240 / 21 / 5 / 48 / 3):
     - claims_total drops > 20 %
     - claims_REPEATED drops > 20 %
     - claims_CONTRADICTS_FACTS drops > 20 %
     - concepts_count drops > 20 %
     - all_violations rises > 20 %

Either failure mode → revert to Qwen3.6-27B-FP8 and document the
cause.

## Sequenced work

1. **Pull the model.** `huggingface-cli download Qwen/Qwen3.6-35B-A3B`
   into `${STORAGE_ROOT}/shared/models/`. Verify weights land + size
   matches (~35 GB FP8 or ~70 GB BF16).
2. **Register in `wiki-compiler/configs/models.yml`.** Add an entry
   matching the existing schema (active_id, served_name, model
   path, context_size, YaRN factor if needed).
3. **Update `.env.active-model`** to point at the new model id +
   served name. Verify `make preflight` GREEN.
4. **Bring vLLM down + up.**
   `make wiki-compiler-down && make wiki-compiler`. Verify
   `/v1/models` returns the new served name and `make smoke` is 8/8.
5. **Microbench decode + prefill.** Run the throughput-bench script
   that produced 47 tok/s for 27B-FP8 (decode-heavy + prefill-heavy
   tests). Record raw rates.
6. **Falsify gate-1?** If decode < 80 tok/s here, stop and revert.
   No need to run a full pilot.
7. **Pilot v6** — full 7-source module 005 run with the new model.
   Use the existing pilot driver, no orchestrator changes. Wall
   time + per-source metrics captured automatically.
8. **Compare to pilot v5 baseline** (canonical at
   `kurpatov-wiki-wiki:canonical/qwen3.6-27b-fp8/module-005/2026-04-27`).
   Use `bench_grade.py --compare-with` for the structural numbers.
9. **Decide:** if both gates passed, swap is canonical for module
   006+. If either failed, revert.

## Expected outcomes

If the hypothesis holds:
- Pilot wall drops from 169 min → 50-90 min per module.
- Architect-velocity (capability-advances per architect-hour) roughly
  doubles, since pilot iteration cost is roughly halved.
- The G2 outcome moves the *throughput* quality dimension of
  Service Operation from ~47 tok/s (Level 1) to ≥ 100 tok/s
  (Level 2). The capability description in Phase B updates
  accordingly when L2 lands.
- Cost-per-output-token drops proportionally to throughput rise
  (same 400 W draw, more tokens out).

If falsified:
- Either MoE doesn't fit our particular vLLM version + driver +
  Blackwell combo, or the model's quality doesn't survive the
  domain transfer to wiki-compilation. We learn which, and which
  next-step is worth pursuing (vLLM upgrade? Smaller dense?).

## Cross-references

- Phase B capability whose throughput dim this advances:
  `phase-b-business-architecture/capabilities/service-operation.md`
  (when that file is populated).
- Phase D technology service whose component this swaps:
  `phase-d-technology-architecture/` § LLM inference (currently in
  forge AGENTS.md Phase D).
- Phase F sibling experiment (closed):
  `G1-blackwell-stability.md` — same capability, different
  quality dim (stability, now at Level 1). G2 advances throughput
  dimension on top of the Level-1-stability foundation G1 closed.
- Pilot v5 baseline metrics (the comparison target):
  `phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/STATE-OF-THE-LAB.md`.
