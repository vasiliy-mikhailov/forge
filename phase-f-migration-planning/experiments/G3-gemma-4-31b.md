# G3 — Faster inference via dense Gemma-4-31B (revert: keep Qwen-27B)

Closed-falsified Phase F experiment. Tested swapping the LLM
component behind the LLM-inference technology service (Phase D)
from Qwen3.6-27B-FP8 to google/gemma-4-31B-it (BF16 source, vLLM
runtime FP8 quant), to test whether dense Gemma offers a quality
edge worth a small wall regression — given G2 already established
that decode rate is not the binding lever for pilot wall.

This is a Phase F doc — Phase B's capability stays the same;
Phase D's tech service stays the same; only the *component*
realising the service was swapped (and reverted).

## Context

G2 (closed 2026-04-27) falsified the MoE-throughput hypothesis:
Qwen3.6-35B-A3B got 4.1× decode but produced 1/7 sources verified
on the pilot, with +1900 % concept violations. The G2 closure
identified per-claim overhead — not decode rate — as the binding
lever for pilot wall (`embed_helpers.py` cold-fork at 5 s/claim,
`factcheck.py` HTTP at 5-15 s/claim, sub-agent delegation at
30 s/concept).

G3's question was different from G2: not "is a faster model
better?" but "is a different *dense* model with potentially better
domain-fit better?" Gemma-4-31B is +15 % parameters over Qwen-27B,
with similar memory-bandwidth profile (so similar decode ceiling),
but a different training distribution.

## Hypothesis (IF–THEN–BECAUSE)

> **IF** we swap the served model from Qwen3.6-27B-FP8 to
> Gemma-4-31B-it (BF16 source, vLLM runtime FP8 quant), keeping
> the Blackwell at the 400 W cap, persistence-mode, vLLM 0.19.1,
> and the rest of the stack unchanged,
>
> **THEN** decode throughput will be approximately equal to or
> ~10 % below Qwen-27B-FP8 (predicted by memory bandwidth ÷
> weight size), pilot wall on a small N=2 module-005 subset will
> stay within ±20 % of pilot v5 baseline, and quality (claims
> shape, structural compliance, concepts cross-ref integrity)
> will hold within ±20 % of pilot v5.
>
> **BECAUSE** Gemma's instruction-tuning may produce tighter
> claim-shape output that compensates for the slightly slower
> decode, AND because the canonical-skill-v2 contract is enforced
> by structural verifier rather than by model preference, quality
> should be model-agnostic at the structural level.

## Falsification criteria

Run a small (N=2 sources) pilot v7 against module 005 with
Gemma-4-31B and compare to pilot v5's published metrics. Falsify
if **any** of:

1. **Throughput floor not reached.** Decode throughput < 30 tok/s
   batch=1 on the Blackwell at 400 W cap. (Floor relaxed vs G2's
   80 tok/s — for G3 we already accept Gemma is no faster than
   Qwen at the decode level; we just need it to *work*.)
2. **Verify rate regression.** < 2/2 sources verified=ok in the
   small pilot.
3. **Structural-compliance regression > 5×** vs v5 baseline. v5
   averaged 3/7 = 0.4 violations per source. Gate at > 2
   violations per source (5× the v5 rate).
4. **Cross-reference integrity regression.** v5 had 0 missing-
   concept-file cross-refs. Gate at > 0 such cross-refs in the
   N=2 pilot — these are load-bearing for the wiki's
   reader-experience contract.

## Sequenced work

1. Pull `google/gemma-4-31B-it` weights into
   `${STORAGE_ROOT}/shared/models/`. Verify size (~62 GB BF16).
2. Register `gemma-4-31b-fp8` entry in
   `phase-c-information-systems-architecture/application-architecture/wiki-compiler/configs/models.yml`
   (FP8 runtime quant, gemma4 tool-call parser, no reasoning
   parser, YaRN factor 1.0 since Gemma already supports 128K
   natively).
3. Fix `--reasoning-parser` flag handling in
   `bin/load-active-model.sh` + `docker-compose.yml` so that
   `reasoning_parser: null` produces a clean omission of the flag
   (vLLM rejects the flag with no value). See ADR amendment to
   model registry.
4. Update `forge/.env`: `INFERENCE_ACTIVE_MODEL_ID=gemma-4-31b-fp8`.
5. `make wiki-compiler-down && make wiki-compiler`. Verify
   `/v1/models` returns `gemma-4-31b-fp8`.
6. Microbench decode + prefill (gate-1).
7. Add `D8_PILOT_SOURCES_LIMIT` env var to `run-d8-pilot.py` for
   small-N quality probes; run pilot v7 with N=2.
8. Grade pilot v7 with `bench_grade.py`; compare to v5 baseline.
9. **Decide:** if all gates passed, plan a full N=7 pilot. If
   any gate failed, revert to Qwen3.6-27B-FP8.

## Closure (2026-04-28)

**FALSIFIED. Gate 4 triggered (cross-reference integrity).
Reverted active model to Qwen3.6-27B-FP8.**

### Gate-1 — microbench

PASS (with adjusted expectation).

| metric                | Qwen-27B-FP8 | Gemma-4-31B-FP8 | delta  |
|-----------------------|--------------|------------------|--------|
| decode tok/s, n=3 avg | 47.0         | **42.3**         | −10 %  |
| prefill tok/s (cache) | ~30 K        | ~30 K            | flat   |
| GPU util / power      | 100% / 400 W | 100% / 400 W     | same   |

The 10 % decode regression is exactly what the memory-bandwidth
ceiling predicts: 47 × (27/31) ≈ 41 tok/s, and we measured 42.3.
Gemma is dense-as-expected.

### Gate-2 — verify rate

PASS. **2/2 sources verified=ok** in pilot v7
(`experiment/D8-pilot-2026-04-28-gemma-4-31b-fp8`).

### Gate-3 — structural compliance

FAIL. v5 baseline was 3 violations across all 7 sources (0.4 per
source). Pilot v7 N=2 produced **17 cross-ref violations + 2
concept-shape violations = 19 total in 2 Gemma sources** (9.5
per source, ~24× the v5 rate).

### Gate-4 — cross-reference integrity

FAIL. v5 had 0 missing-concept-file cross-refs. Pilot v7 SRC 0
(Gemma) declared `concepts_touched` for 17 concept slugs that
were never created as concept files —
`neurotic-style-of-life`, `brain-mechanism`,
`behavior-perspective`, `systemic-perspective`,
`content-perspective`, `functional-perspective`,
`structural-perspective`, `dynamic-stereotype`,
`principle-of-dominant`, `three-story-brain-model`,
`reptilian-brain`, `neocortex`, `cortical-column`,
`self-preservation-instinct`, `sexual-instinct`,
`psychological-chimera`, `pathogenetic-psychotherapy`,
`symptomatic-psychotherapy`. Each is a 404 link in the rendered
wiki — a load-bearing reader-experience break.

### Wall

Gemma is **faster** despite the decode regression:

| metric                | v5 Qwen avg | v7 Gemma avg | delta |
|-----------------------|-------------|--------------|-------|
| wall per source       | ~24 min     | **13.5 min** | −45 % |
| sub-agent calls / src | ~8          | ~6-7         | small drop |

This confirms (again) the G2 close-out: per-claim overhead, not
decode rate, dominates pilot wall. Gemma's edge here is fewer
sub-agent loops + tighter output — the model thinks faster than
Qwen even though each token is slower.

### Why Gemma was a net loss

Same root cause as G2: **the model thinks faster than the
verifier audits.** Gemma produced complete-looking source.md
files with rich `concepts_touched` lists, but the concept-curator
sub-agent did not actually create the corresponding concept files
for many of those slugs. The structural verifier
(`bench_grade.py`) catches this only after the fact; the agent
sub-loop is shorter than the verification loop.

This is a *contract enforcement* problem, not a model-quality
problem. The same Gemma model with a tighter pre-write check
(verify each `concepts_touched` slug has either a corresponding
concept file written *in this source-author run* or already
exists from prior sources) would likely close gate-4.

### Implications for Service Operation capability trajectory

Throughput dimension stays at Level 1 (47 tok/s decode, Qwen-27B)
for production pilots. Component swap to Gemma does NOT advance
the throughput dimension under the current contract-enforcement
mechanism.

The architectural lesson, now twice-confirmed (G2 + G3), is that
**model swaps cannot move pilot wall further** until the
canonical-skill-v2 contract enforcement is moved earlier in the
sub-agent loop. Candidates for the next Phase F experiment
(targeted at *contract enforcement*, not model swap):

- **Pre-write concept-file existence check.** Before
  source-author writes `concepts_touched: [a, b, c]`, the curator
  sub-agent must have created or confirmed each slug's file.
- **Run-level cross-ref linter.** Run `bench_grade.py
  --check-xrefs-only` after each source's commit, fail-fast if
  cross-refs are broken; agent retries with explicit feedback.
- **Daemonize embed_helpers + factcheck cache.** Independent
  lever — reduces per-claim overhead, opens the door for a
  re-test of model swap under tighter contract enforcement.

Once any of those land, a future Phase F experiment can re-test
the Gemma component swap.

## Cross-references

- Phase B capability whose throughput dim this targeted:
  [`../../phase-b-business-architecture/capabilities/service-operation.md`](../../phase-b-business-architecture/capabilities/service-operation.md).
- Phase D technology service whose component this swapped:
  [`../../phase-d-technology-architecture/services/llm-inference.md`](../../phase-d-technology-architecture/services/llm-inference.md).
- G1 closure (stability dim — closed):
  [`G1-blackwell-stability.md`](G1-blackwell-stability.md).
- G2 closure (MoE swap — falsified, same failure mode):
  [`G2-MoE-faster-inference.md`](G2-MoE-faster-inference.md).
- ADR 0009 (architect-edit-loop ssh ControlMaster, opened
  during this experiment):
  [`../../phase-d-technology-architecture/adr/0009-ssh-controlmaster-for-architect-edit-loop.md`](../../phase-d-technology-architecture/adr/0009-ssh-controlmaster-for-architect-edit-loop.md).
- Pilot v5 baseline metrics (the comparison target):
  `experiment/D8-pilot-2026-04-27-qwen3.6-27b-fp8` on
  `kurpatov-wiki-wiki`, tagged
  `canonical/qwen3.6-27b-fp8/module-005/2026-04-27`.
- Pilot v7 experiment branch:
  `experiment/D8-pilot-2026-04-28-gemma-4-31b-fp8` on
  `kurpatov-wiki-wiki`.
