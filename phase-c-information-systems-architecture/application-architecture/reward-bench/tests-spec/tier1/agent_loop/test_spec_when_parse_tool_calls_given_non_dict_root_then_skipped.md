# `test_when_parse_tool_calls_given_non_dict_root_then_skipped`
Sibling of [`test_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising`](test_spec_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising.md).
robustness: when the JSON body inside a fenced ```` ```tool ````
block parses successfully but the root is NOT a dict (e.g. a JSON
array, string, or number), the parser MUST skip the block and emit
no tool observation.
Rationale: the tool wire format mandates `{"name":..., "args":...}`.
A non-dict root cannot be a tool call.
- **Arrange**: a reply with a fenced `tool` block containing
 `[1, 2, 3]` or `"oops"` as the body.
- **Act**: `parse_tool_calls(reply)`.
- **Assert**: returns `[]`; no exception.
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
