# `test_when_execute_submission_observation_observed_then_mean_feeds_best_dev_mean_tracker`

Pins the **active-path** equivalent of cycle-34's
[`_parse_dev_runner_summary`](../../../../src/tier1/agent_loop.py)
which only matches the legacy bash-stdout `MEAN=N.N MEDIAN=... max-tile-best=N`
format. Per [ADR 0008](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md)
the active tool `execute_submission` returns a JSON observation
wrapped in `<observation>...</observation>`. Its `mean` field carries
the dev-mean signal that needs to feed:

- cycle-48 best-snapshot tracker (`_best_dev_mean`)
- cycle-50 finish-floor seam
- cycle-34 supervisor sweep accumulator

So `run_loop` MUST recognise BOTH observation shapes and feed them
into the same accumulator.

- **Arrange**: stub `_call_model` to emit a scripted sequence under
  the active path:
    1. `execute_submission` returning JSON observation with `mean=1000`,
       `max_tile_best=256`, `walltime_sec_total=1.5`.
    2. `execute_submission` returning JSON with `mean=500` (regression).
    3. `finish`.
  Stub `execute_tool` to return the scripted observations.
  Inject a stub `_RecordingSupervisor` that captures every sweep.
- **Act**: `run_loop(..., max_iters=10, supervisor=stub,
  supervisor_every_k=1, finish_floor=0.0)`.
- **Assert**:
  - Captured sweep contains TWO samples whose `mean_score` matches
    [1000.0, 500.0] (active-path parser fired).
  - `[harness] new best dev MEAN=1000` was printed (cycle-48 snapshot
    path triggered).
  - `workspace/submission.best.py` exists (snapshot was saved).

Sibling test pins the malformed-JSON path returns no parse (gracefully
falls through; the dispatcher in cycle 51 already handles JSON safely).

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

