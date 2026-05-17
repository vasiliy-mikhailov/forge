# `test_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising`
Pins the **parser robustness** seam introduced
(discovered live measurement). When a model reply
contains a fenced ```` ```tool ```` block whose body is not valid
JSON (e.g. unterminated string), `parse_tool_calls` MUST:
 - NOT raise `json.JSONDecodeError`;
 - skip that block and emit no tool observation;
 - continue parsing subsequent blocks in the same reply.
Before the live trial 1 crashed the whole
bench process when a single malformed block surfaced. This test
is the regression guard.
Replaces the orphaned [`test_spec_when_tool_block_contains_malformed_json_then_parser_skips_block_and_emits_no_tool_observation`]() — same contract, accurate test name.
- **Arrange**: a reply with a fenced `tool` block containing
 malformed JSON (e.g. unbalanced braces).
- **Act**: `parse_tool_calls(reply)`.
- **Assert**: returns `[]` (empty list); no exception escapes.
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising`.
