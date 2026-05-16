# `test_when_first_reply_at_campaign_temperature_then_majority_views_skill_or_writes_valid_solver`

Stochastic sibling of [`test_when_first_reply_received_then_views_skill_spec_or_writes_protocol_valid_solver`](
test_spec_when_first_reply_received_then_views_skill_spec_or_writes_protocol_valid_solver.md).
Cycle 56 + 62: pins the same first-reply contract at the **campaign
temperature** (`temperature=0.7`, per [ADR 0003](../../../../docs/adr/0003-bench-defaults-500-iters-10-trials-temp-0.7.md)).

Why a separate test: at `temperature=0.0` the contract holds
trivially (greedy decode is repeatable). At `temperature=0.7` we
need a **majority-of-N-draws** check: across N independent first
replies, MORE than half MUST either (a) view `SKILL_tier1.md`
or (b) emit a protocol-valid Solver via `execute_submission`.

This guards against a regression where higher temperature drifts
the model into pure prose or no-tool replies.

- **Arrange**: spawn N concurrent first replies via the live
  vLLM fixture at `temperature=0.7`.
- **Act**: parse each reply for view(SKILL) or execute_submission
  with protocol-valid Solver.
- **Assert**: majority (`>N/2`) satisfy at least one condition.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

