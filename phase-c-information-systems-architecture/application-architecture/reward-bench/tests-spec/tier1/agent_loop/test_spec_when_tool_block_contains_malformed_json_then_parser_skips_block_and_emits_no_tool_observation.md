# `test_when_tool_block_contains_malformed_json_then_parser_skips_block_and_emits_no_tool_observation`

Pins the **tool-call parser robustness** seam. The parser wraps
`json.loads` in
`try/except json.JSONDecodeError` plus a `rstrip(', \t\n')` fallback,
then `continue`s past the bad block. Our parser raises
`JSONDecodeError` which crashes the entire trial in
`src/reward_bench/use_cases/run_bench_trials.py`.

`parse_tool_calls` MUST be defensive: bad JSON in one block must not
abort the iteration. The model gets the standard "no tool calls" error
observation and is given another turn to recover.

- **Arrange**: stub `_call_model` to return a reply whose tool block
  has extra trailing text after the JSON (the exact failure shape from
  cycle 50): `'''```tool\\n{"name": "view", "args": {"path": "/x"}}\\nextra text\\n```'''`.
  Then a valid view on the next turn so the loop progresses.
- **Act**: `run_loop(..., max_iters=3, max_no_tool_call_iters=0)`.
- **Assert**:
  - `run_loop` returns WITHOUT raising `JSONDecodeError`.
  - First iteration's observation messages contain
    `'no tool calls found'` (the parser-skipped block led to an empty
    tool-call list).
  - Second iteration's tool dispatch proceeded normally
    (we can verify by `result['iterations'] == 3`).

Sibling test (kept simple): `parse_tool_calls` returns `[]` (not
raise) when given a single malformed block.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
