# `test_when_extract_fenced_python_called_with_multiple_blocks_then_returns_last_block`

Per [`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4: agents may show intermediate iterations before their final
answer. When multiple fenced blocks appear in the assistant
message, the **last** one is the answer.

- **Arrange**: message string containing three `\`\`\`python`
  blocks tagged `FIRST`, `SECOND`, `THIRD`.
- **Act**: `extract_fenced_python(msg)`.
- **Assert**: returned body is `'THIRD\n'`.

Test code: [`../../../../tests/reward_bench/adapters/test_extract_fenced_python.py`](../../../../tests/reward_bench/adapters/test_extract_fenced_python.py)::`test_when_extract_fenced_python_called_with_multiple_blocks_then_returns_last_block`.

## Model client injection point

None — pure string helper.

## Runtime scope

> **Runtime scope**: unit only — pure function.
