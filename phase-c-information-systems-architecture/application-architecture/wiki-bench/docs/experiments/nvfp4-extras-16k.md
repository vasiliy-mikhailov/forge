# Speed-bench: 4 new NVFP4/AWQ candidates at 16K context — 2026-05-05

Per the inference-mode model registry. Sweep run 2026-05-05 on `rtx-6000-pro-blackwell` (sm_120) under vLLM `0.20.0-cu130-ubuntu2404`, `kv_cache_dtype=fp8`, single-stream + batch=8 on the canonical workload triplet (matches `2026-05-04-nvfp4-16k`).

Bench client now bypasses Caddy by hitting `vllm-inference:8000` directly via `proxy-net` — Caddy hangs proxying chat/completions for non-Qwen models in our setup; using the container IP avoids that whole class of bug.

Artifacts: `${STORAGE_ROOT}/labs/wiki-bench/experiments/2026-05-05-nvfp4-extras-16k/`.

## Headline

| Model | Quant | Decode peak (16k→5k, c=1) | Prefill total (16k→32, c=1) | Batch total (4k→1.25k, c=8) | Median ITL c=8 (ms) |
|---|---|---:|---:|---:|---:|
| **Qwen 3.6-27B** | **AWQ-INT4** | **75** ⭐ | 25 141 | 1 496 | 15.3 |
| Devstral-Small 2-24B | NVFP4 | 72 | **33 932** ⭐ | **1 934** ⭐ | 15.9 |
| Qwen 3.5-27B | NVFP4 | 47 | 19 810 | 1 223 | 23.6 |
| Nemotron-Super 49B | NVFP4 | 35 | 17 178 | 1 000 | 30.6 |

⭐ = best in column among new cells. Combined with May-04 sweep:

| Model (decode peak ranked) | Quant | Decode peak |
|---|---|---:|
| Qwen 2.5-7B | NVFP4 | 214 |
| Qwen 2.5-14B | NVFP4 | 113 |
| Mistral-Nemo-12B | NVFP4 | 110 |
| **Qwen 3.6-27B** | **AWQ-INT4** | **75** ✨ new |
| **Devstral-Small 2-24B** | NVFP4 | **72** ✨ new |
| Mistral-Small 3.2-24B | NVFP4 | 70 |
| Qwen 3.6-27B | NVFP4 | 66 |
| Qwen 3.6-27B | FP8 | 50 |
| Gemma 3-27B | FP8 | 48 |
| Gemma 4-31B | FP8 | 47 |
| **Qwen 3.5-27B** | NVFP4 | **47** ✨ new |
| Qwen 3-32B | FP8 | 40 |
| Gemma 4-31B | NVFP4 | 38 |
| **Nemotron-Super 49B** | NVFP4 | **35** ✨ new |
| Llama 3.3-70B | NVFP4 | 25 |
| Qwen 2.5-72B | NVFP4 | 24 |
| Llama 3.3-70B | FP8 | 21 |
| Qwen 2.5-72B | FP8 | 20 |

## Key findings

1. **AWQ-INT4 is the new fastest decode for Qwen 3.6-27B** at 75 tok/s — beating both NVFP4 (66) and FP8 (50) of the same model. AWQ Marlin kernels on Blackwell are very competitive. Worth re-evaluating "NVFP4 is always best" defaults.
2. **Devstral-Small 2-24B-NVFP4 wins on prefill** at 33 932 tok/s — 50 % faster than Qwen 3.6-27B-NVFP4 (22 822) of similar size. Code-tuned Mistral architecture is prefill-friendly; the heads-and-layers shape favours throughput on this hardware.
3. **Qwen 3.5-27B-NVFP4 (kaitchup pack) is ~30 % slower than Qwen 3.6-27B-NVFP4** despite identical params. The kaitchup pack uses NVFP4-A16 (FP16 activations) — keeping activations at FP16 costs throughput vs full NVFP4. The ekg of "all-NVFP4 is faster than NVFP4-A16" is a real signal.
4. **Nemotron-Super 49B-NVFP4** lands at 35 tok/s decode — between Llama 3.3-70B-NVFP4 (25) and Gemma 4-31B-NVFP4 (38). The NAS-derived 49B size sits exactly where the param-count would predict on this throughput curve. NVIDIA's "fits a single H200 at high workload" claim translates to "fits the Blackwell solo at decent throughput".

## Failures and notes

- **Devstral-2-123B-AWQ-4bit (cyankiwi pack)** — was the most interesting cell to bench (only 123B class model that fits the Blackwell solo at INT4). Two issues stalled it:
  - cyankiwi's repo includes BOTH `consolidated-*` (Mistral native, ~32 GB) AND `model-*` (HF format, ~62 GB) shards. The default `hf download` pulls all of it. We added `--exclude "consolidated*"` to fix.
  - HF rate-limits the cyankiwi bucket. Download stalled at 37 GB / 62 GB after ~10 min.
  Stale download container holds files. Will resume once HF cooldown lifts.

- **Caddy hang for non-Qwen models** — separate vLLM bug worth filing upstream. Hitting `inference.mikhailov.tech/v1/chat/completions` from the host hangs > 30 s for Mistral/Llama/Devstral models. Hitting the container IP directly returns in 0.5 s. Probable cause: Caddy buffering on a header or content-type that triggers a Caddy 2.10 streaming bug. Bench bypasses Caddy.

## Methodology notes

- All cells share max_model_len=32768, kv_cache_dtype=fp8, gpu_memory_utilization=0.92, tensor_parallel_size=1.
- `--enable-prefix-caching --enable-auto-tool-choice --trust-remote-code` enabled at server.
- Bench client: `vllm bench serve --backend openai-chat --base-url http://vllm-inference:8000 --tokenizer <hf_path> --trust-remote-code --ignore-eos`.
- Tokenizers loaded from local HF cache to avoid network at bench time.

## Cross-references

- [2026-05-04-nvfp4-16k](../../../../labs/wiki-bench/experiments/2026-05-04-nvfp4-16k/) — companion sweep covering 10 base models
- [models.yml](../../../../wiki-compiler/configs/models.yml) — current registry (14 entries, all quantized)
- [ADR 0027 quantisation default](../../../../phase-preliminary/adr/0027-quant-default.md)
