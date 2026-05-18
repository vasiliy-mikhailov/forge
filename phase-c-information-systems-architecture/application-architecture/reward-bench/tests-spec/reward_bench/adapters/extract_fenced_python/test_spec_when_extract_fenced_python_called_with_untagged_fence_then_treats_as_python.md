# `test_when_extract_fenced_python_called_with_untagged_fence_then_treats_as_python`

Per [`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4: some agents omit the language tag when their answer is
unambiguous. Bare `\`\`\` ... \`\`\`` fences are accepted as
python.

- **Arrange**: message string containing one untagged `\`\`\`
  ... \`\`\`` block.
- **Act**: `extract_fenced_python(msg)`.
- **Assert**: returned body is `'class Solver: pass\n'`.

Test code: [`../../../../tests/reward_bench/adapters/test_extract_fenced_python.py`](../../../../tests/reward_bench/adapters/test_extract_fenced_python.py)::`test_when_extract_fenced_python_called_with_untagged_fence_then_treats_as_python`.

## Model client injection point

None — pure string helper.

## Runtime scope

> **Runtime scope**: unit only — pure function.
