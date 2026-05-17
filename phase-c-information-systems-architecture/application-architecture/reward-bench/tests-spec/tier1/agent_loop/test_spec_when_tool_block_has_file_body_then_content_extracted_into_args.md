# `test_when_tool_block_has_file_body_then_content_extracted_into_args`
Pins parser body-region: when a fenced ` ```tool ``` ` block contains
the production `===FILE_BODY===` separator after the JSON, the raw
text after the separator goes into `args["content"]` of the parsed
tuple, exactly as documented in `SYSTEM_PROMPT`.
- **Arrange**: a captured-style reply string with one tool block of the
 shape:
 ```tool
 {"name": "execute_submission", "args": {}}
 ===FILE_BODY===
 from __future__ import annotations
 SOLVER = 42
 ```
- **Act**: `parse_tool_calls(reply)`.
- **Assert**: exactly one tuple `('execute_submission', args)` where
 `args["path"] == "/workspace/submission.py"` and `args["content"]`
 starts with `from __future__ import annotations`.
Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).
