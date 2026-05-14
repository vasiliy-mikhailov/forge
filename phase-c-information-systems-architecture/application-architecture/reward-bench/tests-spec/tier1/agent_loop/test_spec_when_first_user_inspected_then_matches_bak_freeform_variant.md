# `test_when_first_user_inspected_then_includes_skill_spec_reference_and_active_tool_hint`

Pins [`FIRST_USER`](../../../../src/tier1/agent_loop.py) to TWO
shape requirements (not a literal equality, which would block ADR-0008
migration):

1. It MUST tell the model to read `/tasks/2048/SKILL_tier1.md` — the
   spec containing the Solver/move/W/A/S/D contract that the cycle-53
   [`validate_submission_protocol`](../../../../src/tier1/harness.py)
   checks against. Without this reference the model writes whatever
   shape its prior wants (observed in cycles 39/49/54: Gym-style
   `def solve(grid) -> int`).
2. It MUST hint at the active tool to use for shipping the submission.
   Under [ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md)
   that's `execute_submission`. Under the legacy path (kept behind
   `--legacy-write-file`) it's `write_file submission.py`. Either
   mention satisfies this requirement; the test must NOT require a
   specific literal.

Why two requirements instead of literal equality: cycle 39 pinned
FIRST_USER to the `_bak` freeform variant, which was the right choice
THEN (matching legacy). ADR 0008 now mandates the prompt evolves to
include `execute_submission` as the primary action. A literal-equality
test would block that evolution; this shape test does not.

- **Arrange**: import `FIRST_USER`.
- **Act**: read the string.
- **Assert**:
  - `'/tasks/2048/SKILL_tier1.md'` appears in `FIRST_USER`.
  - Either `'execute_submission'` OR `'/workspace/submission.py'`
    appears (legacy-or-active tool hint).
  - String length is reasonable: roughly 50-1200 chars (not empty,
    not a code stub injection).

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
