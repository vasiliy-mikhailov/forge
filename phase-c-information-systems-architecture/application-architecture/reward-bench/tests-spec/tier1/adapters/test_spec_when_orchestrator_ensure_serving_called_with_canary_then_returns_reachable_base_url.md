# `test_spec_when_orchestrator_ensure_serving_called_with_canary_then_returns_reachable_base_url`
The cycle-122 live-runtime test for
[`InferenceOrchestrator`](../../../src-spec/ports/inference_orchestrator/src_spec_when_inference_orchestrator_ensure_serving_called_then_returns_base_url.md)
via its production binding
[`DockerVllmInferenceOrchestrator`](../../../src/tier1/adapters/docker_vllm_inference_orchestrator.py).
Actually invokes the orchestrator against the real Docker + vLLM
stack and verifies `/v1/models` advertises `target.served_name`.
Companion test pins idempotency: two consecutive `ensure_serving`
calls with the same target must return the same URL without
restarting the container.
Pins the live-test runtime of the contract per
[AGENTS](../../../../../AGENTS.md#three-runtimes-two-scales-of-src_spec--unit--live--production).
Unit-runtime variants live in
[`test_inference_orchestrator_di.py`](../../../tests/adapters/test_inference_orchestrator_di.py)
(4 monkeypatched / Protocol-existence tests). Production-runtime
coverage is the canonical bench itself
([`run_canonical_battery()`](../../../src/reward_bench/frameworks/run_battery.py)
invokes `_default_inference_orchestrator()` per model swap).
## Contract
- **Arrange**: instantiate `DockerVllmInferenceOrchestrator()` (no
 monkeypatch); pick the lab canary `qwen3.6-27b-awq` from
 `MODEL_REGISTRY`.
- **Act**: `orchestrator.ensure_serving(target)`. May take seconds
 (idempotent if container already serves target) or minutes (cold
 vLLM provision + warmup).
- **Assert**:
 - return is a `str` starting with `http://` and containing `:8000`
 - `GET {base_url}/v1/models` returns 200
 - response body contains `target.served_name`
Companion test (idempotency):
- **Arrange**: same orchestrator + target.
- **Act**: call `ensure_serving(target)` twice.
- **Assert**: both calls return the same URL (no container restart
 between them).
Test code:
[`tests/tier1/adapters/test_docker_vllm_inference_orchestrator_live.py`](../../../tests/tier1/adapters/test_docker_vllm_inference_orchestrator_live.py).
## Runtime injection points
| runtime | adapter binding | config / target |
|------------|---------------------------------------|---------------------------|
| unit | `FakeInferenceOrchestrator` (autouse) | scripted base_url; arbitrary target |
| **live** | `DockerVllmInferenceOrchestrator` | canary `qwen3.6-27b-awq` from MODEL_REGISTRY |
| production | `DockerVllmInferenceOrchestrator` | every model in MODEL_REGISTRY (one swap per model in canonical bench) |
## Runtime scope
> **Runtime scope**: unit only — tier1 adapter contract; @live coverage at the production-scale boundary per the relevant cycle (123/124/125/128).

Test code: [`../../../tests/tier1/adapters/test_docker_vllm_inference_orchestrator_live.py`](../../../tests/tier1/adapters/test_docker_vllm_inference_orchestrator_live.py)::`test_when_orchestrator_ensure_serving_called_with_canary_then_returns_reachable_base_url`.
