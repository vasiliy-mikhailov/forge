# `test_when_score_submission_called_with_env_that_hangs_one_game_then_returns_within_aggregate_walltime_budget`

Reproduces the cycle-26 real-system bug: cycle 23 added a
`hard_wall_sec` AGGREGATE cap checked **between games**, but a
single `play_one_game` call that hangs (or sleeps very long) blocks
the cap because the check never fires while inside `play_one_game`.
Per [ADR 0006 layer 1](../../../../docs/adr/0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md),
the aggregate cap is necessary but not sufficient.

This cycle adds **per-game preemption**: each `play_one_game` call
runs in a daemon thread with a join timeout derived from the
remaining budget. If the thread doesn't return in time, the use
case abandons it (it stays alive but the process exits when
pytest does) and emits a sentinel `GameResult(final_state='walltime_exceeded')`.

- **Arrange**: stub env whose `play_one_game(seed=1)` calls
  `time.sleep(1000)` (simulates a hung game); other seeds return
  immediately. `hard_wall_sec=0.3`. 3 seeds (the hang is on the
  first).
- **Act**: invoke `score_submission(...)` inside a daemon thread
  with a `1.0 s` join timeout. Pre-fix this never returns because
  the inner stub blocks for 1000 s.
- **Assert**:
  - The outer wrapper thread completed (`done is True`).
  - `result.walltime_exceeded is True`.
  - The first game has `final_state == 'walltime_exceeded'` (the
    hung-game sentinel).
  - Subsequent seeds are NOT necessarily exceeded; if remaining
    budget allows, they run normally. With `hard_wall_sec=0.3`
    and seed 1 burning the budget, seeds 2-3 also fall through
    to the aggregate-cap path.

This is the **proper layer-1 fix** to the cycle-26 hang. The
Docker sandbox (ADR 0006 layer 2) is still queued as the
SPEC.md-canonical isolation path.

Test code: [`tests/tier1/use_cases/test_score_submission.py`](../../../../tests/tier1/use_cases/test_score_submission.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

