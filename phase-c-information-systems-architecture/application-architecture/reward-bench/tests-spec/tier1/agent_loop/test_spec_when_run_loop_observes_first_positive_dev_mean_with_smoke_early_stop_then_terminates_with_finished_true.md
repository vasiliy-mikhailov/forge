# `test_when_run_loop_observes_first_positive_dev_mean_with_smoke_early_stop_then_terminates_with_finished_true`

Pins the **smoke early-stop seam** in
[`run_loop`](../../../../src/tier1/agent_loop.py) per
[ADR 0009 v2](../../../../docs/adr/0009-multi-model-smoke-bench-convention.md).

When `run_loop` is invoked with `smoke_early_stop=True` and an
`execute_submission` observation produces `dev_mean > 0`, the loop
MUST terminate with `finished=True` regardless of the model's
`finish` decision. The cycle-48 best-snapshot machinery still
fires; the cycle-65 finish-time promotion still fires.

Rationale: with the v2 smoke convention's `max_iters=100`, strong
models would otherwise grind to iter 100 (or model-decided
finish, which in cycle 71 trial 2 was iter 74) before canonical
scoring runs. Early-stop says: *"once we've proven the model can
produce a positive solution, we're done — stop spending compute"*.

- **Arrange**: monkeypatch `_call_model` to return canned
  assistant replies that emit:
    - iter 1: an `execute_submission` whose mocked observation
      carries `dev_mean = 100.0` (first positive).
    - iter 2 and beyond: more replies (would normally continue).
  Monkeypatch `execute_tool` to return a synthetic
  `<observation>{"mean": 100.0, ...}</observation>` for the
  first `execute_submission` call.
- **Act**: `run_loop(..., max_iters=10, smoke_early_stop=True)`.
- **Assert**:
  - `result["finished"] is True`.
  - `result["iterations"] == 1` (loop exited after the first
    positive-dev iter).
  - `_call_model` was called **exactly once** for the assistant
    reply at iter 1 (no second call).
  - The best snapshot `submission.best.py` exists in workspace
    (cycle 48 path fired).

Negative control: with `smoke_early_stop=False` (default), the
same arrangement runs the full `max_iters=10`. (Already pinned by
existing cycle-48 best-snapshot test.)

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — agent-loop seam wiring contract; live coverage via the @live agent_loop tests in tests/tier1/test_agent_loop.py (skill_prompt_sent_then_reply_contains_tool_call_block, first_reply_received_then_views_skill_spec, run_loop_invoked_with_one_iter_cap_then_returns_one_turn_history).

