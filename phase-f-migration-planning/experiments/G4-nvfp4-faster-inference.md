# G4 — Faster inference via NVFP4 (4-bit weights on Blackwell tensor cores)

Closed (2026-05-03). Verdict: **PASS — promote NVFP4 as default**.

## Context

Per [G2 closure](G2-MoE-faster-inference.md), MoE was falsified as the
binding throughput lever for the wiki-compile pilot wall. G4 tests the
adjacent lever: same dense 27 B Qwen 3.6 architecture, but quantize
weights to NVFP4 (4-bit, NVIDIA microscaling format, native on Blackwell
sm_120 tensor cores via FLASHINFER_CUTLASS).

The arithmetic predicts a roughly 2× memory-bandwidth uplift:
30.9 GB FP8 → 19 GB NVFP4 → fewer bytes loaded per matmul → faster
both prefill (compute-bound but weights still streamed) and decode
(memory-bandwidth-bound).

## Hypothesis (IF–THEN–BECAUSE)

- **IF** we replace the FP8 weights of Qwen 3.6-27B with the NVFP4
  variant `sakamakismile/Qwen3.6-27B-NVFP4` (compressed-tensors /
  nvfp4-pack-quantized format), keeping `max_model_len`, KV-cache dtype,
  GPU memory utilization, chat template, and tool-call parser identical,
- **THEN** single-stream decode tokens/sec rises ≥ 15 %, prefill
  throughput rises ≥ 25 %, and TTFT on long prompts (4 K) falls ≥ 25 %
  vs the FP8 baseline,
- **BECAUSE** Blackwell sm_120 has native FP4 tensor-core throughput
  ~2× FP8, and weight bytes loaded per token drops by ~38 %.

## Method

Two `vllm bench serve --dataset-name random --ignore-eos` runs on the
same Blackwell card, same vLLM 0.19.1, same `max_model_len=262144`, same
`gpu_memory_utilization=0.92`, same `kv_cache_dtype=fp8`. Three
scenarios per run:

| Scenario | Input | Output | n | Concurrency | Probes |
|---|---|---|---|---|---|
| decode-heavy | 64 | 1024 | 16 | 1 | decode TPS, TPOT |
| prefill-heavy | 4096 | 32 | 16 | 1 | prefill TPS, TTFT |
| realistic batch | 1024 | 128 | 64 | 8 | aggregate TPS under load |

Plus a 5-prompt quality sanity probe on the FP8 baseline (`fp8-quality.log`).

## Result

Full numbers: `${STORAGE_ROOT}/labs/wiki-bench/experiments/2026-05-03-fp8-vs-nvfp4/RESULTS.md`.

Hypothesis was met or exceeded on every clause:

- Single-stream decode TPS: **45.46 → 56.00 tok/s (+23.2 %)** — beats the +15 % bar
- Prefill TPS: **2 978 → 4 227 tok/s (+41.9 %)** — beats the +25 % bar
- TTFT (4 K prompt, mean): **705 → 421 ms (−40.3 %)** — beats the −25 % bar
- Batch-c8 aggregate output throughput: **219 → 289 tok/s (+31.8 %)**
- Per-token decode latency (TPOT): **21.96 → 17.77 ms (−19.1 %)**
- Disk size: 30.9 GB → 19 GB
- KV-cache concurrency at 256 K: 6.09× → 7.26× (smaller weights leave
  more VRAM for KV at the same `gpu_memory_utilization`)

## Decision

`INFERENCE_ACTIVE_MODEL_ID` flipped from `qwen3.6-27b-fp8` to
`qwen3.6-27b-nvfp4` in `forge/.env`. The FP8 entry stays in
`configs/models.yml` as a fallback if NVFP4 quality regressions surface
in production (revert is `INFERENCE_ACTIVE_MODEL_ID=qwen3.6-27b-fp8 &&
make stop-all && make inference`).

## Caveats / what we didn't measure

- **Quality A/B was skipped.** Decision made on throughput alone per
  architect call ("let's stick to 4bit"). If wiki-compile output
  concept-recall regresses on T4 grading vs the existing FP8 baseline,
  the verdict gets revisited and FP8 returns. The 5-prompt FP8 quality
  probe is preserved as a comparison baseline if needed.
- **Different quantization toolchains.** FP8 from Qwen team AutoFP8;
  NVFP4 from llmcompressor (community / sakamakismile). Calibration
  corpus differs — quality deltas would conflate calibration noise with
  bit-width effects.
- **KV cache stays FP8 in both.** The win is concentrated on weight
  bandwidth and matmul; KV ops are unchanged.

## Cross-references

- [G2 — MoE swap (FALSIFIED)](G2-MoE-faster-inference.md) — the
  alternative throughput lever that didn't pan out
- [phase-d/services/llm-inference.md](../../phase-d-technology-architecture/services/llm-inference.md) — service that this experiment lifts
- [phase-c-…/operating-modes/inference/SPEC.md](../../phase-c-information-systems-architecture/operating-modes/inference/SPEC.md) — operating mode where the swap was validated
- [`configs/models.yml`](../../phase-c-information-systems-architecture/application-architecture/wiki-compiler/configs/models.yml) — registry; both entries (fp8 + nvfp4) coexist

## Measurable motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: pilot wall on 7-source modules is decode-bound (G1/G2 prior
  closures); raising single-stream decode TPS shortens pilot wall.
- **Goal**: [TTS](../../phase-a-architecture-vision/goals.md) (KR:
  tts_share ≥ 0.30). Faster decode → faster end-to-end wiki-compile
  pipeline → better time-to-source.
- **Outcome**: NVFP4 weights provide +23 % decode TPS / +42 % prefill TPS
  on the same hardware with no architecture-layer changes.
- **Measurement source**: experiment-closure: G4.
- **Contribution**: closes the throughput-via-quantization adjacent
  experiment after G2's MoE-swap falsification; gets us closer to the
  L2 decode target (≥ 100 tok/s) without changing the model architecture.
- **Capability realised**: [Service operation](../../phase-b-business-architecture/capabilities/service-operation.md).
- **Function**: Quantize-weights-to-FP4-on-Blackwell.
- **Element**: this experiment file + `RESULTS.md`.
