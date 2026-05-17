# `test_when_structured_parser_arguments_is_dict_then_used_directly`

Pins the non-strict vLLM branch: when `function.arguments` arrives as
a Python dict already (some vLLM modes skip the JSON encoding), the
parser uses it as the args directly.

## Contract

- **Arrange**: `reply = _reply(tool_calls=[{'type': 'function',
  'function': {'name': 'finish', 'arguments': {'note': 'done'}}}])`.
- **Act**: `StructuredOpenAIParser().extract(reply)`.
- **Assert**: returns `[('finish', {'note': 'done'})]`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_structured_parser_arguments_is_dict_then_used_directly`.

## Runtime scope

> **Runtime scope**: unit only.
