# qwen3.6-27b-bf16 — bench spec addendum

Inherits SPEC.md.

## Identity
served_name:  qwen3.6-27b-bf16
hf_path:      Qwen/Qwen3.6-27B
family:       qwen3.5 (mamba-transformer hybrid)
quant:        bf16
vram_budget:  ~ 53 GB on Blackwell (BF16, mamba-hybrid)
tool_parser:  qwen3_coder

## Hardware
primary:  blackwell (lab container vllm-inference)
fallback: none on 5090 (BF16 does not fit 32 GB)

## Currently served
container: vllm-inference
ip:        resolved at test time via docker inspect
port:      8000

## Family-derived constraints
Inherits spec/families/qwen3.5.md when it is born. Until that file
exists, the relevant fact is captured below.

- Mamba-Transformer hybrid → vLLM auto-scales block_size to 2096.
  Requires --max-num-batched-tokens >= 4096 in serve_flags to avoid
  silent validator hang (vllm#36697).

## Known issues
None observed at Step 1. (Step 2 and Step 3 tests will populate this
section if the model misbehaves.)
