# `test_when_build_condenser_called_with_target_then_returns_llm_condenser_for_same_model_per_adr_0001`
Pins that `main`'s `_build_condenser(target, base_url, api_key)`
helper returns an `LlmCondenser` whose `model_id` equals the bench
`ModelTarget.id`. This is the executable encoding of
[SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md):
"the condenser uses the same `ModelTarget` as the model under
bench".
- **Arrange**: import `_build_condenser` and `LlmCondenser` and
 construct a `ModelTarget` for `qwen3.6-27b-awq`.
- **Act**: `condenser = _build_condenser(target, 'http://stub',
 'unused')`.
- **Assert**:
 - `isinstance(condenser, LlmCondenser)`.
 - `condenser.model_id == target.id`.
This test does NOT invoke the live LLM — the `summarise` callable
inside the returned `LlmCondenser` is only exercised when the agent
loop actually triggers compaction. The cycle-12 live test will
exercise it end-to-end at session boundary.
Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.

Test code: [`../../../../tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py)::`test_when_build_condenser_called_with_target_then_returns_llm_condenser_for_same_model_per_adr_0001`.
