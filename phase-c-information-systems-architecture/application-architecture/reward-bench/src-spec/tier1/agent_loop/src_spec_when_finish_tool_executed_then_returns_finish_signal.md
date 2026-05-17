# `src_spec_when_finish_tool_executed_then_returns_finish_signal`
`execute_tool('finish', args,...)` returns the string
`<finish>{args.get("note", "")}</finish>`. No state mutation. The
loop driver detects the `<finish>` tag in the observation and breaks
the loop. The submission file currently at `/workspace/submission.py`
is what gets scored downstream.
