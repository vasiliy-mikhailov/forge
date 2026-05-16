# `test_when_model_registry_inspected_then_lab_live_model_qwen3_6_27b_awq_present`

Pins the lab's actually-running model in the registry. The
reward-bench-vllm container (per `src/tier1/inference.py`) serves
`qwen3.6-27b-awq` from `cyankiwi/Qwen3.6-27B-AWQ-INT4`. The
end-to-end bench test discovered this entry was missing from
`MODEL_REGISTRY` — drift between the inference framework file and
the registry would let the bench reference an unregistered model.

- **Arrange**: import `MODEL_REGISTRY` from
  `src.reward_bench.use_cases.model_registry`.
- **Act**: look up the entry with `id == 'qwen3.6-27b-awq'`.
- **Assert**:
  - the entry exists.
  - `hf_path == 'cyankiwi/Qwen3.6-27B-AWQ-INT4'`.
  - `served_name == 'qwen3.6-27b-awq'`.
  - `max_model_len == 131072`.
  - `tool_call_parser == 'qwen3_coder'`.

Test code: [`tests/reward_bench/use_cases/test_model_registry.py`](../../../../tests/reward_bench/use_cases/test_model_registry.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — MODEL_REGISTRY tuple contract; pure-Python data; scale-invariant.

