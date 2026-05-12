# `src_spec_when_bench_provisions_inference_then_qwen3_6_27b_awq_serves_with_128k_context`

`bench.tier1.inference.ensure_serving()` brings the lab vLLM container
up if it is not already up, and returns the URL at which it is
reachable. Idempotent.

Configuration encoded in code:

- Container name: `reward-bench-vllm` (lab-owned).
- Docker network: `proxy-net`.
- GPU: Blackwell (resolved via `$GPU_BLACKWELL_UUID` env).
- Image: `vllm/vllm-openai:v0.20.0-cu130-ubuntu2404`.
- Model: `cyankiwi/Qwen3.6-27B-AWQ-INT4`, served as `qwen3.6-27b-awq`.
- `--max-model-len 131072` (SPEC.md Tier 1 author-stage budget).
- `--max-num-batched-tokens 4096` (Mamba/attention page alignment, vllm#36697).
- `--max-num-seqs 128` (Mamba decode cache blocks).
- `--kv-cache-dtype fp8`.
- `--gpu-memory-utilization 0.85`.
- `--enable-prefix-caching`, `--enable-auto-tool-choice`,
  `--tool-call-parser qwen3_coder`, `--trust-remote-code`.
- HF token from `$HF_TOKEN`.
- API key from `$VLLM_API_KEY`.

Health probe: poll `/v1/models` once every 10 s for up to 6 min.
Container is considered serving when 200 AND `qwen3.6-27b-awq` appears
in `data[].id`.

Idempotency:
- Container exists and healthy: return URL.
- Container exists but unhealthy / exited: `docker rm -f` and recreate.
- Container does not exist: create.
