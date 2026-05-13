# `src_spec_when_fenced_python_extracted_then_compiles_without_syntax_error`

`src.tier1.adapters.parser.extract_python(reply: str) -> str` returns the body
of the first fenced Python code block found in `reply`. The body is
the text between the opening ` ```python ` (or ` ``` `) and the
matching closing ` ``` `, exclusive.

If no fenced Python block is found, raises `ValueError`.

The returned string must compile via `compile(body, '<sub>', 'exec')`.
The parser does not enforce this directly; the test asserts it.
