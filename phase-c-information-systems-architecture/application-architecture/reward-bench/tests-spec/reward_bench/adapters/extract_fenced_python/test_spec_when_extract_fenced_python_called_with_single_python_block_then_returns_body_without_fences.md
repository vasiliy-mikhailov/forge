# `test_when_extract_fenced_python_called_with_single_python_block_then_returns_body_without_fences`

Per [`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4 binding: the agent emits its final Solver code in a fenced
```` ```python ... ``` ```` block in its last assistant message.
`extract_fenced_python` lifts the body out, stripped of fence
markers and the language tag.

- **Arrange**: message string containing one `\`\`\`python` block
  with a Solver class inside.
- **Act**: `extract_fenced_python(msg)`.
- **Assert**: returned body equals the inner text, no fence
  markers, no `python` language tag.

Test code: [`../../../../tests/reward_bench/adapters/test_extract_fenced_python.py`](../../../../tests/reward_bench/adapters/test_extract_fenced_python.py)::`test_when_extract_fenced_python_called_with_single_python_block_then_returns_body_without_fences`.

## Model client injection point

None — pure string helper.

## Runtime scope

> **Runtime scope**: unit only — pure function.
