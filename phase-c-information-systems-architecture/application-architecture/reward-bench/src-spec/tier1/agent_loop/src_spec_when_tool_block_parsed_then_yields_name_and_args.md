# `src_spec_when_tool_block_parsed_then_yields_name_and_args`
`src.tier1.agent_loop.parse_tool_calls(reply: str) -> list[tuple[str, dict]]`
returns one `(name, args)` tuple per ` ```tool... ``` ` fenced block
found in `reply`. The block body is JSON of the form
`{"name": "...", "args": {...}}`. The fence body MAY include a
`===FILE_BODY===` line followed by raw file content — when present
that body content goes into `args["content"]`. Cycles covering body
extraction come later; the current cycle pins only the no-body case
(view, bash, finish).
If no fence found, returns `[]`.
