# `test_when_fenced_python_extracted_then_compiles_without_syntax_error`

Pins parser layer L4.1: the Python source extracted from the model's
fenced reply parses as valid Python.

- **Arrange**: session-scoped `skill_tier1_reply` fixture (live model
  call, shared across L3.2–L6.2).
- **Act**: call `src.tier1.parser.extract_python(reply)` to get the
  fence body, then `compile(source, '<solver-submission>', 'exec')`.
- **Assert**: `compile` returns a code object (does not raise
  `SyntaxError`).

Test code: [`tests/tier1/test_parser.py`](../../tests/tier1/test_parser.py).
