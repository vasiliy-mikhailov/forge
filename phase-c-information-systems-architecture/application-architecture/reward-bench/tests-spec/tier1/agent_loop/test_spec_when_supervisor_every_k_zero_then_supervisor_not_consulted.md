# `test_when_supervisor_every_k_zero_then_supervisor_not_consulted`

Pins the **back-compat / default-off** path for the supervisor
hook (cycle 33, [ADR 0005](../../../../SOLUTION-ARCHITECTURE.md)).

When `supervisor_every_k=0` (the BenchConfig default), the bench
MUST never call the supervisor — regardless of whether one is
passed. This preserves cycle-12 behaviour and lets callers run the
bench without an ADR-0005 plateau-detection consult.

- **Arrange**: pass a recorder supervisor that asserts on call.
- **Act**: `run_loop(..., supervisor=recorder, supervisor_every_k=0)`
  with `max_iters >= 5`.
- **Assert**: recorder was called zero times after the loop ends.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

