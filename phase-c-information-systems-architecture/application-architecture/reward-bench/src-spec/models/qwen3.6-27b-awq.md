# qwen3.6-27b-awq — bench spec addendum

Inherits SPEC.md.

## Identity

Canonical fields (`id`, `hf_path`, `served_name`, `tool_call_parser`,
`max_model_len`) live in
[`MODEL_REGISTRY`](../../src/reward_bench/use_cases/model_registry.py).
This data sheet captures only the operational / family-quirk facts
the registry can't carry:

- family:      qwen3.5 (mamba-transformer hybrid)
- vram_budget: ~ 18 GB on 5090 (AWQ, mamba-hybrid)

## Hardware
primary:  rtx-5090 (playground container omega-reptile-vllm-playground)
fallback: blackwell (also fits trivially)

## Currently served
container: omega-reptile-vllm-playground
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
