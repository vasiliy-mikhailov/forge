# `test_when_parse_tool_calls_given_non_dict_root_then_skipped`

Sibling of [`test_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising`](
test_spec_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising.md).
Cycle 51 robustness: when the JSON body inside a fenced ```` ```tool ````
block parses successfully but the root is NOT a dict (e.g. a JSON
array, string, or number), the parser MUST skip the block and emit
no tool observation.

Rationale: the tool wire format mandates `{"name": ..., "args": ...}`.
A non-dict root cannot be a tool call.

- **Arrange**: a reply with a fenced `tool` block containing
  `[1, 2, 3]` or `"oops"` as the body.
- **Act**: `parse_tool_calls(reply)`.
- **Assert**: returns `[]`; no exception.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
