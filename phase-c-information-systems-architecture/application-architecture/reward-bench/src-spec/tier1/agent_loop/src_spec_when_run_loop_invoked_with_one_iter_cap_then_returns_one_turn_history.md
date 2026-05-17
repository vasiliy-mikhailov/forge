# `src_spec_when_run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history`
`src.tier1.agent_loop.run_loop(workspace, env_dir, tasks_dir,
vllm_base_url, vllm_api_key, max_iters=1)` orchestrates:
1. Initialize `messages = [{system: SYSTEM_PROMPT}, {user: FIRST_USER}]`.
2. Loop until `max_iters` reached or any tool call is `finish`:
 - POST `messages` to `{vllm_base_url}/v1/chat/completions` with
 model `qwen3.6-27b-awq`, `max_tokens=32768`, `temperature=0.0`.
 - Append assistant reply to `messages`.
 - Call `parse_tool_calls(reply)`. If none, append an error
 observation telling the model to use the tool format.
 Otherwise call `execute_tool(name, args,...)` for each.
 - Append a single user message with all observations joined by
 blank lines.
3. Return `{iterations, messages, finished}`.
This is the smallest cycle: one full turn (model call + observe).
Multi-turn iteration uses the same loop body — no new code, just a
larger `max_iters` and a finish-detection branch (already pinned
upstream by L0).
