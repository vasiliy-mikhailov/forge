# `test_when_structured_arguments_contains_sentencepiece_space_then_stripped_before_parsing`

Pins the mistral-leak workaround in the legacy shim: SentencePiece
artefacts `Ġ` (U+0120) and `▁` (U+2581) inside the JSON-string
`function.arguments` are stripped before `json.loads`.

## Contract

- **Arrange (case 1)**: `structured` with arguments
  `'{"path":\u0120"SKILL_tier1.md"}'` (U+0120 between `:` and value).
- **Act**: `parse_tool_calls('', structured_tool_calls=structured)`.
- **Assert**: `calls == [('view', {'path': 'SKILL_tier1.md'})]`.
- **Arrange (case 2)**: same but with `\u2581` instead.
- **Act + Assert**: same expected output.

## Model client injection point

- **Seam**: none — pure function.

Test code: [`../../tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py)::`test_when_structured_arguments_contains_sentencepiece_space_then_stripped_before_parsing`.

## Runtime scope

> **Runtime scope**: unit only.
