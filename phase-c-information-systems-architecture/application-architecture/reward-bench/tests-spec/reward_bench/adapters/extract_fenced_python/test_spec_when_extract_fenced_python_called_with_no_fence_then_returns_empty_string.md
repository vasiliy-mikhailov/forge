# `test_when_extract_fenced_python_called_with_no_fence_then_returns_empty_string`

Per [`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4: when the agent's last message contains no fenced block, the
helper returns `''`. The orchestrator continues; the Runner
scores the empty body (it will score 0); the loop advances.

- **Arrange**: message string with no fence at all.
- **Act**: `extract_fenced_python(msg)`.
- **Assert**: returned body is `''`.

Test code: [`../../../../tests/reward_bench/adapters/test_extract_fenced_python.py`](../../../../tests/reward_bench/adapters/test_extract_fenced_python.py)::`test_when_extract_fenced_python_called_with_no_fence_then_returns_empty_string`.

## Model client injection point

None — pure string helper.

## Runtime scope

> **Runtime scope**: unit only — pure function.
