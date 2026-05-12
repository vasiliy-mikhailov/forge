# Test cases — SPEC.md

These are the test cases that prove a model card satisfies the bench
contract in SPEC.md.

All tests parameterize over every card in spec/models/*.md.

## Step 1 — model responds at all

- test_when_card_served_then_v1_models_returns_served_name
- test_when_card_prompted_with_hello_then_response_is_non_empty

## Step 2 — model emits a tool call (future, not yet implemented)

- test_when_card_prompted_with_tool_request_then_response_contains_fenced_tool_block
- test_when_response_parsed_then_yields_one_tool_call_named_view

## Step 3 — single agent step (future, not yet implemented)

- test_when_view_tool_called_then_executor_returns_file_contents
- test_when_step_complete_then_followup_prompt_reaches_model
