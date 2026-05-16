# `src_spec_when_inference_orchestrator_ensure_serving_called_then_returns_base_url`

[`InferenceOrchestrator`](../../../src/ports/inference_orchestrator.py)
— the runtime-boundary Port for "(re)provision the inference backend
to serve `target`; return its base URL." Created in cycle 117 as
part of the ADR 0018 backsweep — wraps the pre-existing
`ensure_serving_model` free function in
`src/tier1/inference.py`.

## Contract

```python
class InferenceOrchestrator(Protocol):
    def ensure_serving(self, target: ModelTarget) -> str: ...
```

Semantics:

- `target` is a [`ModelTarget`](../../../src/reward_bench/entities/model_target.py)
  carrying `id`, `hf_path`, `served_name`, `tool_call_parser`, and
  `max_model_len` — everything the adapter needs to start the model.
- Return is the base URL (no trailing slash) once the backend
  advertises `target.served_name` at `/v1/models`. Subsequent
  callers can issue chat-completion requests against the URL.

### Liveness / failure semantics

- **MAY raise `TimeoutError`** if the backend doesn't become healthy
  within the adapter's configured timeout. Treat as infrastructure
  failure — no in-loop recovery.
- **MUST be idempotent.** Repeat calls for the same `target` while
  the container is already serving it return the same URL without
  re-spawning.
- **MUST NOT raise on transient infrastructure quirks** that the
  adapter can paper over (port not yet open during boot, etc.).
  Retry-with-deadline lives inside the adapter.

## Adapter manifest

- [`DockerVllmInferenceOrchestrator`](../../../src/tier1/adapters/docker_vllm_inference_orchestrator.py)
  — production binding. Delegates to `ensure_serving_model` which
  spawns/reconciles the `reward-bench-vllm` Docker container per
  [ADR 0001](../../../docs/adr/0001-condenser-uses-same-model-as-bench.md)
  +
  [ADR 0006](../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md).
- [`FakeInferenceOrchestrator`](../../../src/adapters/fakes/fake_inference_orchestrator.py)
  — test adapter. Records calls on `self.calls`, returns scripted
  `base_url`, configurable to raise `TimeoutError` for specific
  `served_name`s.

Enforcement:
[`test_when_runtime_boundary_port_inspected_then_protocol_exists[InferenceOrchestrator]`](../../../tests/architecture/test_runtime_boundary_ports.py)
asserts the Protocol exists;
[`test_when_runtime_boundary_port_has_fake_then_fake_class_importable[InferenceOrchestrator]`](../../../tests/architecture/test_runtime_boundary_ports.py)
asserts the Fake is importable. DI tests in
[`test_inference_orchestrator_di.py`](../../../tests/adapters/test_inference_orchestrator_di.py)
assert both adapters expose the Port surface.

## Follow-up: migrate callers to Port DI

Today `main.py` imports `ensure_serving_model` as a free function;
the conftest autouse fixture monkeypatches it for tests. A follow-up
cycle can:
  1. Add an `inference_orchestrator: InferenceOrchestrator` parameter
     to `main()` defaulted via a `_default_inference_orchestrator()`
     factory (parallel to the cycle-109 canonical_scorer pattern).
  2. Add an autouse conftest fixture binding `FakeInferenceOrchestrator`
     for non-live tests.
  3. Remove the existing monkeypatch dance in conftest.

That cycle is deferred per cycle-113 minimal-implementation
discipline — the Port lift is structural; the call-site migration is
a separate concern with its own RED → GREEN → REFACTOR.
