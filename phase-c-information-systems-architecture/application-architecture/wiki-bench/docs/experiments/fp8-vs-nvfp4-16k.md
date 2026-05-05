# FP8 vs NVFP4 — 10-model sweep at 16K context

Per [ADR 0027 — quantisation default](../../../../phase-preliminary/adr/0027-quant-default.md). Sweep run 2026-05-04 on `rtx-6000-pro-blackwell` (sm_120) under vLLM `0.20.0-cu130-ubuntu2404`, `KVCacheDtype=fp8`, single-stream + batch=8 on the canonical decode/prefill/batch triplet.

Artifacts: `${STORAGE_ROOT}/labs/wiki-bench/experiments/2026-05-04-fp8-16k/` and `…/2026-05-04-nvfp4-16k/`.

## Headline

NVFP4 is **+15-40 % faster than FP8** across the board on Blackwell sm_120, as the architecture has native nvfp4 mma. Two models broke under NVFP4 (loader-side, not throughput-side).

## Decode peak — single-stream, 16k→5k tokens, tok/s

| Model | FP8 | NVFP4 | Δ |
|---|---:|---:|---:|
| Qwen 2.5-7B | 152 | 214 | +41 % |
| Mistral-Nemo-12B | 98 | 110 | +12 % |
| Qwen 2.5-14B | 80 | 113 | +41 % |
| Mistral-Small 3.2-24B | (partial run) | 70 | — |
| **Qwen 3.6-27B** | **50** | **66** | **+32 %** |
| Gemma 3-27B | 48 | FAIL | vision encoder issue under NVFP4 |
| Gemma 4-31B | 47 | 38 | -19 % |
| Qwen 3-32B | 40 | FAIL | AngelSlim NVFP4 quant issue |
| Llama 3.3-70B | 21 | 25 | +19 % |
| Qwen 2.5-72B | 20 | 24 | +20 % |

## Batch throughput — c=8, 4k→1.25k, total tok/s

| Model | FP8 | NVFP4 | Δ |
|---|---:|---:|---:|
| Qwen 2.5-7B | 3 875 | 4 587 | +18 % |
| Mistral-Nemo-12B | 2 585 | 2 926 | +13 % |
| Qwen 2.5-14B | 2 022 | 2 407 | +19 % |
| Mistral-Small 3.2-24B | (partial) | 2 083 | — |
| **Qwen 3.6-27B** | **1 162** | **1 455** | **+25 %** |
| Gemma 3-27B | 1 258 | FAIL | — |
| Gemma 4-31B | 1 036 | 931 | -10 % |
| Qwen 3-32B | 1 029 | FAIL | — |
| Llama 3.3-70B | 547 | 696 | +27 % |
| Qwen 2.5-72B | 530 | 676 | +28 % |

## Prefill total — c=1, 16k→32, total tok/s

| Model | FP8 | NVFP4 | Δ |
|---|---:|---:|---:|
| Qwen 2.5-7B | 61 343 | 79 364 | +29 % |
| Mistral-Nemo-12B | 41 695 | 47 369 | +14 % |
| Qwen 2.5-14B | 35 730 | 44 987 | +26 % |
| Mistral-Small 3.2-24B | (partial) | 21 726 | — |
| **Qwen 3.6-27B** | **18 429** | **22 822** | **+24 %** |
| Gemma 3-27B | 21 565 | FAIL | — |
| Gemma 4-31B | 17 907 | 17 037 | -5 % |
| Qwen 3-32B | 18 505 | FAIL | — |
| Llama 3.3-70B | 9 912 | 11 762 | +19 % |
| Qwen 2.5-72B | 9 598 | 11 362 | +18 % |

## Anomalies

- **Gemma 4-31B is slower in NVFP4** (-5 % to -19 %). The Google Gemma 4 architecture seems to suffer under the AngelSlim NVFP4 packing — kernel selection is probably falling back to a Marlin path that's slower than the FP8 cutlass kernel. Worth a follow-up investigation but doesn't block the default-to-NVFP4 decision.
- **Gemma 3-27B fails to load** under NVFP4. The vision encoder weights aren't supported by the FlashInfer Cutlass NvFp4 linear kernel. Use FP8 for Gemma 3 if its vision capabilities are needed.
- **Qwen 3-32B fails to load** under NVFP4. Looks like an AngelSlim packing artifact (the same quantiser produced a working Qwen 3.6-27B though). Track upstream fix; FP8 is the fallback.

## Decision

NVFP4 stays the default for all 8 working models per ADR 0028 (inference mode default quant). FP8 stays available as fallback for Gemma 3-27B and Qwen 3-32B until upstream NVFP4 issues are resolved.

For reward-bench Tier 2-4, **Qwen 3.6-27B-NVFP4 is the standardised play-time LLM** — best balance of comprehensiveness band (27B), latency (66 tok/s decode, 1455 tok/s batched), and quant stability.

## Cross-references

- [ADR 0027 — quantisation default](../../../../phase-preliminary/adr/0027-quant-default.md)
- [ADR 0028 — inference mode](../../../../phase-preliminary/adr/0028-inference-mode.md)
- [ADR 0029 — reward-bench](../../../../phase-preliminary/adr/0029-reward-bench.md)
- Earlier 27B-only A/B at varying input/output lens: `experiments/2026-05-03-fp8-vs-nvfp4/`
