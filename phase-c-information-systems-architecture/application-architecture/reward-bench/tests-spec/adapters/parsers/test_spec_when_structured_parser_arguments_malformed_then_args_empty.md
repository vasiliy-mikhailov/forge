# `test_when_structured_parser_arguments_malformed_then_args_empty`

Pins the defensive branch: when `function.arguments` is a non-empty
string that fails `json.loads`, the call is still returned but with
empty args (`{}`) — the agent loop sees a name with no parameters
rather than receiving an exception.

## Contract

- **Arrange**: `reply = _reply(tool_calls=[{'type': 'function',
  'function': {'name': 'view', 'arguments': '{not json'}}])`.
- **Act**: `StructuredOpenAIParser().extract(reply)`.
- **Assert**: returns `[('view', {})]`. No exception.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_structured_parser_arguments_malformed_then_args_empty`.

## Runtime scope

> **Runtime scope**: unit only.
