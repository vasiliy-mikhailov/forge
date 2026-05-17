# `test_when_structured_parser_arguments_contain_sentencepiece_space_then_stripped`

Pins the mistral-tokenizer-leak workaround: SentencePiece artefacts
`Ġ` (U+0120) and `▁` (U+2581) inside the JSON-string
`function.arguments` are stripped to a regular space before
`json.loads`, so the args parse correctly.

## Contract

- **Arrange**: `reply = _reply(tool_calls=[{'type': 'function',
  'function': {'name': 'view', 'arguments': '{"path":Ġ"SKILL_tier1.md"}'}}])`.
- **Act**: `calls = StructuredOpenAIParser().extract(reply)`.
- **Assert**: `calls == [('view', {'path': 'SKILL_tier1.md'})]`.

## Model client injection point

- **Seam**: none — pure function over `AssistantReply`.

Test code: [`../../../tests/adapters/parsers/test_protocol_parser_adapters.py`](../../../tests/adapters/parsers/test_protocol_parser_adapters.py)::`test_when_structured_parser_arguments_contain_sentencepiece_space_then_stripped`.

## Runtime scope

> **Runtime scope**: unit only.
