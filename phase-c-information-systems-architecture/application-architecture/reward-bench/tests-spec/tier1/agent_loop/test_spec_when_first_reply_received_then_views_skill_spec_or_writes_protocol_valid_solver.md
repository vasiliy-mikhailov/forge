# `test_when_first_reply_received_then_views_skill_spec_or_writes_protocol_valid_solver`

The **prompt is software**: per the user CATS principle that surfaced
in cycle 56, the SYSTEM_PROMPT + FIRST_USER pair MUST cause the model
under test to either:

  (a) **view** `/tasks/2048/SKILL_tier1.md` to read the protocol — or
  (b) directly **write_file** a `/workspace/submission.py` whose body
      passes [`validate_submission_protocol`](../../../../src/tier1/harness.py)
      (class Solver + move(self, board) -> 'W'|'A'|'S'|'D')

on the FIRST reply. If neither happens, the prompt is broken — the
test goes RED and we iterate on the prompt until GREEN.

This closes the user-identified gap from cycle 54: cycle 53's
validator only flagged invalid submissions AFTER the run; cycle 55's
campaign guard only flagged campaigns where ALL trials failed. Cycle
56 catches the bug at the source — the prompt itself failing to
instruct the model into reading the spec.

- **Arrange**: import `SYSTEM_PROMPT`, `FIRST_USER`, `_call_model`,
  `parse_tool_calls`, `validate_submission_protocol`,
  `load_submission`. Send the prompt pair to the live vLLM at
  `temperature=0.0` (deterministic).
- **Act**: parse the first reply into tool calls.
- **Assert**:
  - At least one tool call returned.
  - First tool call is either:
      - `view` with `path == '/tasks/2048/SKILL_tier1.md'`, OR
      - `write_file` with `path == '/workspace/submission.py'`
        AND a `content` body whose load+validate yields no violations.

Pytest marker: `@pytest.mark.live` — opt-in, requires
`VLLM_API_KEY` and a healthy vLLM at `reward-bench-vllm`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
