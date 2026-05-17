# `test_when_run_loop_called_with_condense_callable_then_condense_invoked_before_each_call_model`
Pins the **architectural seam** for context compaction: `run_loop`
accepts a `condense` callable parameter and invokes it on the
message history before each `_call_model` request. Default is
identity (no compaction) — behaviour-preserving.
pins ONLY the seam. The LLM-backed condenser adapter and the trigger logic follow. The default
identity behaviour means the cycle-12 end-to-end bench keeps working
without changes.
- **Arrange**: monkeypatch `agent_loop._call_model` to return a
 finish tool block immediately (so the loop exits after one
 iteration without a live vLLM call). Build a recording callable
 that captures every invocation.
- **Act**: `run_loop(workspace,..., max_iters=1, condense=recorder)`.
- **Assert**:
 - The recorder was invoked at least once.
 - Its argument was a tuple of message dicts (the conversation
 history just before `_call_model`).
 - The return value flows back into the loop without disrupting
 the finish path.
Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
Architectural note: agent_loop lives in tier1 (inner module); the
condense parameter is a bare `Callable` (not typed as the outer
module's `CondenserPort`). The orchestrator (`reward_bench.frameworks.main`)
adapts a `CondenserPort` to the callable at the boundary so the
inner-cannot-import-outer rule holds.
Per [SOLUTION-ARCHITECTURE](../../../SOLUTION-ARCHITECTURE.md),
the LLM-backed condenser adapter will use the same
`ModelTarget` as the model under bench; only pins the seam,
the model decision lands when the adapter does.
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_run_loop_called_with_condense_callable_then_condense_invoked_before_each_call_model`.
