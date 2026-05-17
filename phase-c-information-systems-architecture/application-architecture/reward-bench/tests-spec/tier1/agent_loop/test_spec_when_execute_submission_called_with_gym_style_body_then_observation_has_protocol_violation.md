# `test_when_execute_submission_called_with_gym_style_body_then_observation_has_protocol_violation`

Pins the **protocol-violation** branch of the `execute_submission`
dispatcher (cycle 58, [ADR 0008](../../../../SOLUTION-ARCHITECTURE.md))
when the model emits a Gym-style `def solve(state) -> int` instead
of the SKILL_tier1.md contract (`class Solver` + `move(board) -> WASD`).

The dispatcher MUST NOT raise. It MUST return a structured
observation JSON with:
  - `protocol_violations` non-empty, containing a string about the
    missing `Solver` class
  - `per_seed == []`
  - `mean == 0`

This is the cycle-53 contract surfaced through the cycle-58 dispatcher.

- **Arrange**: a body that exports `def solve(state): return 0`
  and nothing else.
- **Act**: `execute_tool('execute_submission', {'content': body},
  workspace, env_dir, tasks_dir)`.
- **Assert**: observation has `protocol_violations` mentioning
  `Solver`, `per_seed == []`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

