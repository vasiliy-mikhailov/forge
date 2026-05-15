# `test_when_system_prompt_inspected_then_advertises_execute_submission_as_primary_tool`

Pins [`SYSTEM_PROMPT`](../../../../src/tier1/agent_loop.py) shape per
[ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md):

- MUST advertise `execute_submission` as a tool with a working example.
- MUST advertise `view` and `finish` (still active per SPEC.md).
- MUST instruct the model to read `/tasks/2048/SKILL_tier1.md`.
- MUST NOT mention `write_file` or `bash` (removed in cycle 92 per
  ADR 0008; ADR 0007 superseded).
- Reasonable length (1000..6000 chars; not empty, not war-and-peace).

Not a literal-equality pin — the prompt evolves. Shape contract.

- **Arrange**: import `SYSTEM_PROMPT`.
- **Act**: read the string.
- **Assert**:
  - `'execute_submission'` appears.
  - `'view'` appears.
  - `'finish'` appears.
  - `'/tasks/2048/SKILL_tier1.md'` appears.
  - `1000 <= len(SYSTEM_PROMPT) <= 6000`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
