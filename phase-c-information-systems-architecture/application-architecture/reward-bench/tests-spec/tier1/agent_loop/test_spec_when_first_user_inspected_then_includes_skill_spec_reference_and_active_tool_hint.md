# `test_when_first_user_inspected_then_includes_skill_spec_reference_and_active_tool_hint`

Pins the **shape** of [`FIRST_USER`](../../../../src/tier1/agent_loop.py)
per cycle 61 (replaces cycle-39's `matches_bak_freeform_variant`
pin which referenced the deleted `_bak/` reference).

FIRST_USER is the message that opens every agent loop. Per cycles
56 + 61 it MUST:
  - point the model at `/tasks/2048/SKILL_tier1.md` as the spec to
    read first;
  - mention `execute_submission` as the active tool ([ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md))
    so the model knows the primary submit path.

This is a non-literal-equality contract — the prompt evolves; the
SHAPE doesn't.

- **Arrange**: import `FIRST_USER` from `src.tier1.agent_loop`.
- **Act**: read the string.
- **Assert**:
  - `'/tasks/2048/SKILL_tier1.md'` appears in `FIRST_USER`.
  - `'execute_submission'` appears in `FIRST_USER`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

