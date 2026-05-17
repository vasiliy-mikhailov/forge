# `test_when_fenced_text_parser_given_filebody_then_content_merged_into_args`

Pins the `===FILE_BODY===` separator contract: when present inside a
```tool block, the text after the separator is merged into the call's
`args['content']`. Enables `execute_submission` to receive the inline
submission body without JSON-escaping.

## Contract

- **Arrange**: `content = '```tool\n{"name": "execute_submission",
  "args": {}}\n===FILE_BODY===\nclass Solver: pass\n```'`.
- **Act**: `calls = FencedTextParser().extract(_reply(content=content))`.
- **Assert**: `len(calls) == 1`; `calls[0].name == 'execute_submission'`;
  `calls[0].args['content'].startswith('class Solver')`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_fenced_text_parser_given_filebody_then_content_merged_into_args`.

## Runtime scope

> **Runtime scope**: unit only.
