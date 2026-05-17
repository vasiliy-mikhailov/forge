# `test_when_max_no_tool_call_iters_exceeded_then_run_loop_terminates`
Pins the cycle-38 stall-detection knob `max_no_tool_call_iters`. When
K consecutive `run_loop` iterations produce no parseable tool call
(model emitting prose only), the loop breaks early with `finished=False`
and the iteration counter at K.
Without this knob the cycle-22 hang shape could re-emerge — a model
generating long prose with no `bash`/`view`/`finish` tool block runs
for the full `max_iters` budget producing nothing useful.
- **Arrange**: stub `_call_model` to return a plain prose string (no
 tool block) on every call. `max_no_tool_call_iters=3`.
- **Act**: `run_loop(..., max_iters=100,
 max_no_tool_call_iters=3)`.
- **Assert**:
 - `result['iterations'] == 3` (stops at K, not 100).
 - `result['finished'] is False`.
 - `_call_model` was invoked exactly 3 times.
Default `max_no_tool_call_iters=0` keeps cycle-12 behavior (never
abort on no-tool-call streaks).
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
