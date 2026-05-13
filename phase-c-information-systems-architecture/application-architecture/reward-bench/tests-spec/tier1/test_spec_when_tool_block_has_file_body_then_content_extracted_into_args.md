# `test_when_tool_block_has_file_body_then_content_extracted_into_args`

Pins parser body-region: when a fenced ` ```tool ``` ` block contains
the production `===FILE_BODY===` separator after the JSON, the raw
text after the separator goes into `args["content"]` of the parsed
tuple, exactly as documented in `SYSTEM_PROMPT`.

- **Arrange**: a captured-style reply string with one tool block of the
  shape:

      ```tool
      {"name": "write_file", "args": {"path": "/workspace/submission.py"}}
      ===FILE_BODY===
      from __future__ import annotations
      SOLVER = 42
      ```

- **Act**: `parse_tool_calls(reply)`.
- **Assert**: exactly one tuple `('write_file', args)` where
  `args["path"] == "/workspace/submission.py"` and `args["content"]`
  starts with `from __future__ import annotations`.

Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).
