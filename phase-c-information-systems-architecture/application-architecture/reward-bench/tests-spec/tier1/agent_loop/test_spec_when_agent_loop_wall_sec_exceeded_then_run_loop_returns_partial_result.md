# `test_when_agent_loop_wall_sec_exceeded_then_run_loop_returns_partial_result`
Pins the cycle-38 stall-detection knob `agent_loop_wall_sec`. When
the total wall time of `run_loop` exceeds this budget (BETWEEN
iterations — checked after each iter completes), the loop terminates
with `finished=False`.
Mirrors `score_submission.hard_wall_sec` but for
the AGENT LOOP rather than the SCORING phase. Together with 's
per-game preemption, this gives end-to-end wall-time bounds for a
trial.
- **Arrange**: stub `_call_model` to return a valid `view` tool call
 but also `time.sleep(0.3)` per call to consume wall time.
 `agent_loop_wall_sec=0.5`, `max_iters=100`.
- **Act**: `run_loop(..., max_iters=100,
 agent_loop_wall_sec=0.5)`.
- **Assert**:
 - `result['iterations'] >= 1` (made some progress).
 - `result['iterations'] < 100` (did NOT run the full budget).
 - `result['finished'] is False`.
Default `agent_loop_wall_sec=0.0` keeps cycle-12 behavior (unbounded).
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_agent_loop_wall_sec_exceeded_then_run_loop_returns_partial_result`.
