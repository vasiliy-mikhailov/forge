# `test_when_parse_tool_calls_given_trailing_comma_then_recovers_via_rstrip`

Sibling of [`test_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising`](
test_spec_when_parse_tool_calls_given_malformed_json_then_returns_empty_list_without_raising.md).
Cycle 51 robustness: when the JSON body inside a fenced ```` ```tool ````
block ends with a trailing comma before `}`, the parser MUST
recover via right-strip-then-retry rather than rejecting the
block. Trailing commas are a common model mistake.

- **Arrange**: a reply with a fenced `tool` block whose body is
  `{"name": "view", "args": {"path": "/tasks/2048/SKILL.md",}}` —
  trailing comma before `}`.
- **Act**: `parse_tool_calls(reply)`.
- **Assert**: returns one tool call `('view', {'path': '...'})`;
  no exception.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

