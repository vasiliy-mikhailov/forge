# `test_when_supervisor_recommends_stop_then_run_loop_terminates_early`

Pins the [ADR 0005](../../../../SOLUTION-ARCHITECTURE.md)
seam in `run_loop`: an optional `supervisor: SupervisorPort` is
consulted every `supervisor_every_k` iterations. When the supervisor
returns `stop_recommended=True`, `run_loop` MUST:

1. Terminate the loop without further `_call_model` invocations.
2. Set `finished=True` in the return dict.
3. Append a synthetic `assistant`-side reasoning trail noting WHY the
   loop ended (the supervisor's `reasoning` text).

This is the application-side counterpart to cycle 32 (LlmSupervisor)
and cycle 31 (NullSupervisor default).

- **Arrange**: monkeypatch `_call_model` to return a reply with one
  tool call that the loop will consume (the simplest: a `view`
  tool — does no harm, observation comes back as an error which is
  fine for the seam test). Inject a stub supervisor that returns
  `SupervisorDecision(plateau=True, stop_recommended=True,
  reasoning='stub stop')` on every `judge` call.
- **Act**: `run_loop(..., max_iters=10, supervisor=stub,
  supervisor_every_k=1)`. With every-iter consult and immediate
  stop recommendation, the loop should exit after iter 1.
- **Assert**:
  - `result['iterations'] == 1`.
  - `result['finished'] is True`.
  - The last message in `result['messages']` mentions the
    supervisor's `reasoning` ('stub stop').
  - `_call_model` was invoked exactly once.

A sibling test pins `supervisor_every_k=0` (default) does NOT consult.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

