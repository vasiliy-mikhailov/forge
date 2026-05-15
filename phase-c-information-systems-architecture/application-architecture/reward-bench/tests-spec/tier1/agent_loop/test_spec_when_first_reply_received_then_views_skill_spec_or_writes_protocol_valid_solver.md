# `test_when_first_reply_received_then_views_skill_spec_or_writes_protocol_valid_solver`

The **prompt is software**: per [ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md)
and the cycle-56 CATS principle, the `SYSTEM_PROMPT + FIRST_USER` pair
MUST cause the model under test to either:

  (a) **view** `/tasks/2048/SKILL_tier1.md` to read the protocol — or
  (b) directly emit a protocol-valid Solver via:
      - **`execute_submission`** (the active tool per ADR 0008) with a
        body whose load+validate yields no
        [`validate_submission_protocol`](../../../../src/tier1/harness.py)
        violations, OR

      - `view` with `path == '/tasks/2048/SKILL_tier1.md'`, OR
      - `execute_submission` with `args['content']` body that
        load+validate yields no violations, OR
      - `write_file` with `path == '/workspace/submission.py'`
        AND body that load+validate yields no violations.

Pytest marker: `@pytest.mark.live` — opt-in, requires
`VLLM_API_KEY` and a healthy vLLM at `reward-bench-vllm`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
