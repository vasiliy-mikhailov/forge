# `src_spec_when_tool_block_has_file_body_then_content_extracted_into_args`
`parse_tool_calls(reply)` splits each fenced tool body on a line
containing exactly `===FILE_BODY===`. Everything before the separator
is JSON; everything after is raw file content, attached to
`args["content"]` (overriding any pre-existing `content` key).
Documented separator is `===FILE_BODY===` (per `SYSTEM_PROMPT` in
`src/tier1/agent_loop.py`).
For blocks without the separator, behavior is unchanged: body is
JSON-only.
Implementation in `src/tier1/agent_loop.py::parse_tool_calls`.
