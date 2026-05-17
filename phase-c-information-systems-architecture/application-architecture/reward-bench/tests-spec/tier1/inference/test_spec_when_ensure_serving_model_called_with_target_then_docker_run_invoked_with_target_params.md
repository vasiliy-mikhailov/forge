# `test_when_ensure_serving_model_called_with_target_then_docker_run_invoked_with_target_params`
Pins `ensure_serving_model(model_target)`: takes a ModelTarget,
(re)provisions the `reward-bench-vllm` container so it serves
`model_target.served_name` with `model_target.hf_path` and
`model_target.tool_call_parser`. Returns the base URL once healthy.
This is the multi-model counterpart to `ensure_serving()`
(qwen3.6-27b-awq hardcoded). 's `test_per_model_bak_runner`
+ this swap helper unblocks scoring every entry in
[`MODEL_REGISTRY`](../../../../src/reward_bench/use_cases/model_registry.py)
per cats.md artifacts-come-from-tests.
Behaviour:
1. If container is running AND healthy AND serves the requested
 `served_name`, return its base URL (no swap).
2. Otherwise, remove the existing container if any and start a new
 one with the target's HF path, served name, max_model_len, and
 tool-call parser. Wait for `/v1/models` to advertise served_name.
This test mocks `subprocess.run` — no real docker calls. It verifies
the command shape (the right --model, --served-model-name,
--tool-call-parser, --max-model-len make it into the docker run
argv).
- **Arrange**: monkeypatch `subprocess.run` to record commands AND
 return synthetic responses (inspect IP, healthy /v1/models with
 served_name in body). Build a ModelTarget for devstral-small-2-24b
 (different parser, different hf_path).
- **Act**: `ensure_serving_model(target)`.
- **Assert**:
 - `docker rm -f reward-bench-vllm` was invoked (swap path).
 - `docker run... --name reward-bench-vllm...` argv contains
 `--model Firworks/Devstral-Small-2-24B-Instruct-2512-nvfp4`,
 `--served-model-name devstral-small-2-24b`,
 `--max-model-len 131072`,
 `--tool-call-parser mistral`.
 - Returns a base URL containing the IP and port 8000.
Test code: [`tests/tier1/test_inference.py`](../../../../tests/tier1/test_inference.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — inference-orchestration wiring contract; @live coverage at the InferenceOrchestrator level.

Test code: [`../../../tests/tier1/test_inference.py`](../../../tests/tier1/test_inference.py)::`test_when_ensure_serving_model_called_with_target_then_docker_run_invoked_with_target_params`.
