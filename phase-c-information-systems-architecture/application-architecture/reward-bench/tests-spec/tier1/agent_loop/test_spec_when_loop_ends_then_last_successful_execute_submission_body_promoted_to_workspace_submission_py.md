# `test_when_loop_ends_then_last_successful_execute_submission_body_promoted_to_workspace_submission_py`
Pins the [ finish-time promotion clause](../../../../SOLUTION-ARCHITECTURE.md#finish-time-promotion-to-workspace-submission-py).
`execute_submission` writes the body to a transient location during
the ralph loop — not directly to `/workspace/submission.py`. But the
canonical scoring path (`GameBoard2048Adapter` →
`load_submission(workspace/submission.py)`) reads exactly that file.
To bridge: `run_loop` MUST remember the body from the most recent
`execute_submission` whose observation had `per_seed` populated (i.e.
the validator passed AND seeds ran), and at end-of-loop (whether
finish-triggered or budget-exhausted), write that body to
`workspace/submission.py`.
If no successful execute_submission ever ran, the file is NOT created
by the loop and canonical scoring emits its standard sentinel
(cycle-53 protocol violation if file missing → "no submission" path).
This works alongside cycle-48 best-snapshot: that mechanism copies
the file produced by ANY write_file (legacy) to.best.py. is the
equivalent for the active path. The two are independent — using
execute_submission, `_best_dev_mean` updates via cycle-63 parser, but
`submission.best.py` may stay empty until also restores its
own snapshot. For this cycle the simpler "last-successful body wins"
rule is sufficient.
- **Arrange**: stub `_call_model` to script TWO execute_submission
 calls (different bodies) and a finish. Stub `execute_tool` to
 return observations: first with `per_seed=[...]` (good), second
 with `per_seed=[]` (protocol violation). Then finish.
- **Act**: `run_loop(..., max_iters=10)`.
- **Assert**:
 - `workspace/submission.py` exists.
 - Its contents equal the body from the FIRST execute_submission call
 (the only one with `per_seed != []`).
Sibling test: when NO execute_submission ever succeeded, no
submission.py is written by run_loop (left to canonical scoring's
sentinel path).
Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

Test code: [`../../../tests/tier1/test_agent_loop.py`](../../../tests/tier1/test_agent_loop.py)::`test_when_loop_ends_then_last_successful_execute_submission_body_promoted_to_workspace_submission_py`.
