# `test_when_score_submission_called_with_slow_env_then_returns_within_aggregate_walltime_budget`

Pins the **cap-API contract** that mitigates the cycle-22 real-system
hang: `score_submission` accepts a `hard_wall_sec` parameter; when
> 0, aggregate walltime is capped; the use case returns within
the budget (plus the cost of one in-flight game). Per
[ADR 0006 layer 1](../../../../SOLUTION-ARCHITECTURE.md).

What this test does **not** do:
- It does NOT literally reproduce a 34-min hang — that would take
  34 minutes. The unit test substitutes a deterministic 0.6 s/game
  stub for cycle-22's heavy-lookahead Solver.
- It does NOT preempt a single hanging game mid-play. The
  aggregate cap fires BETWEEN games. Per-game preemption is the
  Docker tier-1 sandbox layer (ADR 0006 layer 2, queued).

What this test DOES pin:
- Without `hard_wall_sec`, the original cycle-22 call site had no
  cap available; the hang was the operational consequence. Adding
  the parameter is the API-level fix.
- With `hard_wall_sec=0.3`, the use case completes well inside a
  2-second budget despite a 6-second uncapped workload, with
  `AttemptResult.walltime_exceeded=True` and at least one game
  flagged `final_state='walltime_exceeded'`.

- **Arrange**: build a stub `GameEnvPort` (`_SlowEnv`) whose
  `play_one_game` sleeps `0.6 s` per game. Build a 10-seed list
  (~6 s uncapped).
- **Act**: invoke `score_submission(..., hard_wall_sec=0.3)`
  inside a daemon thread with a `2.0 s` join timeout. The
  threaded wrapper ensures a non-cap-honouring implementation
  fails the test without hanging the pytest process.
- **Assert**:
  - The thread completed within 2.0 s (`captured['done'] is True`).
  - No exception was raised inside the thread (catches the
    pre-fix TypeError on the missing kwarg — that's the **failure
    mode** that points at the missing API).
  - `result.walltime_exceeded is True`.
  - At least one game has `final_state == 'walltime_exceeded'`.
  - `result.hard_wall_sec == 0.3`.

Test code: [`tests/tier1/use_cases/test_score_submission.py`](../../../../tests/tier1/use_cases/test_score_submission.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — use-case orchestration; the live coverage for the full scoring path is via @live test_docker_canonical_scorer_live (cycle 123) at the Docker boundary.

