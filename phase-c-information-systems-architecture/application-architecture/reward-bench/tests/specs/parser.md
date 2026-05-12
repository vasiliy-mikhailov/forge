# Test cases — parser

Reverse-engineered from _bak/bin/agent_loop.py (parse_tool_calls + helpers).

## parse_tool_calls

- test_when_reply_has_one_closed_tool_fence_then_returns_one_call
- test_when_reply_has_no_tool_fence_then_returns_empty_list
- test_when_reply_has_two_closed_tool_fences_then_returns_two_calls_in_order
