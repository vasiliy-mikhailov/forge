# `test_when_execute_submission_called_with_syntax_error_body_then_observation_has_syntax_violation`
Pins the **SyntaxError** branch of the `execute_submission`
dispatcher).
When the model emits Python that does not parse, the dispatcher
MUST NOT raise. It MUST return a structured observation JSON with:
 - `protocol_violations` non-empty, containing `'SyntaxError'`
 - `per_seed == []`
 - `mean == 0`
Per [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
sentinel-on-malformed pattern, the bench converts the parse failure
into a structured signal the model can read.
- **Arrange**: a body with malformed Python (e.g. `</body>\n`).
- **Act**: `execute_tool('execute_submission', {'content': body},
 workspace, env_dir, tasks_dir)`.
- **Assert**: observation `protocol_violations` mentions `SyntaxError`,
 `per_seed == []`, `mean == 0`.
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
