# `test_when_llm_supervisor_called_with_plateau_sweep_then_returns_stop_decision_from_reply`
Pins the happy-path round-trip for [`LlmSupervisor`](../../../../src-spec/reward_bench/adapters/llm_supervisor/src_spec_llm_supervisor.md):
sweep tuples render into a JSON-format prompt, the stub
`ask` callable returns a well-formed JSON reply, and the adapter
parses it into a `SupervisorDecision` whose fields match the reply.
- **Arrange**: record the prompt seen by `ask` and return a fixed
 reply that mimics a model's "this is a plateau" verdict:
 `{"plateau": true, "reasoning": "score flat at 3000 for 5 turns",
 "stop_recommended": true}`. Sweep has 3 samples all at 3000.
- **Act**: `decision = LlmSupervisor(ask, 'qwen3.6-27b-awq').judge(sweep)`.
- **Assert**:
 - `decision.plateau is True`.
 - `decision.stop_recommended is True`.
 - `decision.reasoning == 'score flat at 3000 for 5 turns'`.
 - The captured prompt mentions every sweep iteration's score (the
 adapter MUST include the sweep — otherwise the LLM judges blind).
 - The captured prompt contains the string `"plateau"` (the reply
 schema instruction reached the model).
Test code: [`tests/reward_bench/adapters/test_llm_supervisor.py`](../../../../tests/reward_bench/adapters/test_llm_supervisor.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — parser/fallback semantics over scripted replies; live model coverage is via run_loop @live tests.
