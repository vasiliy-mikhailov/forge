# `test_when_system_prompt_inspected_then_advertises_execute_submission_as_primary_tool`

Pins [`SYSTEM_PROMPT`](../../../../src/tier1/agent_loop.py) shape per
[ADR 0008](../../../../SOLUTION-ARCHITECTURE.md):

- MUST advertise `execute_submission` as a tool with a working example.
- MUST advertise `view` and `finish` (still active per SPEC.md).
- MUST instruct the model to read `/tasks/2048/SKILL_tier1.md`.
- MUST NOT mention `write_file` or `bash` (removed in cycle 92 per
  ADR 0008).
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

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

