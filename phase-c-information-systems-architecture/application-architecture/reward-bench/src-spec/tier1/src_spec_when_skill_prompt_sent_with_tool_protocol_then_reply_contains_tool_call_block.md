# `src_spec_when_skill_prompt_sent_with_tool_protocol_then_reply_contains_tool_call_block`

`src.tier1.agent_loop` exposes two module-level constants:

- `SYSTEM_PROMPT` — the system message that instructs the model on
  the fenced-block JSON tool format with `view` / `bash` / `write_file` /
  `finish` tools, the ralph loop, and the dev_runner workflow.
  Lifted verbatim from `_bak/bin/agent_loop.py` (May 2026 production
  campaign that produced the historical ~15.9k mean score on
  Qwen3.6-27B-AWQ).
- `FIRST_USER` — the first user message that bootstraps the task,
  telling the model to read `SKILL_tier1.md` and start iterating.
  Also lifted verbatim.

These constants are the input contract; downstream cycles will add
the parser / executor / loop that consumes the model's tool-call
output. The first cycle just proves the prompt shape elicits tool
use from the live model.
