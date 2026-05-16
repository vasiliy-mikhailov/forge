# `test_when_main_invoked_then_dev_hard_wall_sec_scales_with_canonical_per_game_share`

Pins the **dev/canonical per-game-budget alignment** from cycle 77
(deferred from cycle 70 / ADR 0006).

## Why

The dev feedback path (5 seeds, `DEV_HARD_WALL_S=30`) and the canonical
scoring path (20 seeds, `config.hard_wall_sec`) both pass an aggregate
budget to `score_submission`. Per-game cap derives from `remaining =
aggregate - elapsed`. The effective per-seed share is therefore
`aggregate / n_seeds` on average.

Pre-cycle-77:
- Dev:       30s / 5 seeds = 6 s/seed average.
- Canonical: 60s / 20 seeds = 3 s/seed average (cycle 78 smoke config).

A Solver that runs 5 s/game passes dev but burns canonical's budget
before game 14 → walltime_exceeded sentinels dominate. Cycle 78
leaderboard observed this on `llama-3.3-70b-nvfp4`: dev allowed it,
canonical failed.

## Contract

`main()` derives:
```
dev_hard_wall_sec = config.hard_wall_sec * 5 / len(seeds)
                    when config.hard_wall_sec > 0
                  = None (-> module default 30s)
                    otherwise
```
and threads it into `run_loop(..., dev_hard_wall_sec=...)` →
`execute_tool(..., dev_hard_wall_sec=...)` →
`_execute_submission(..., dev_hard_wall_sec=...)` → `score_submission(...,
hard_wall_sec=dev_hard_wall_sec)`.

Result: dev's per-seed share equals canonical's. A Solver that's too
slow on canonical also gets rejected on dev.

## Tests

### Scale derivation

- **Arrange**: `BenchConfig(hard_wall_sec=60.0)`,
  `seeds=range(1000, 1020)` (20 seeds).
- **Act**: monkeypatch `score_submission` to capture its kwargs; invoke
  `main()` with a fake `run_loop` that calls
  `_execute_submission(body, workspace, tasks_dir, dev_hard_wall_sec=...)`.
- **Assert**: `score_submission` is called with `hard_wall_sec == 15.0`
  (= 60 * 5 / 20) on the dev path.

### Disabled canonical -> module default

- **Arrange**: `BenchConfig(hard_wall_sec=0.0)`.
- **Assert**: dev path uses `DEV_HARD_WALL_S = 30.0` (back-compat).

### Direct unit on _execute_submission

- **Arrange**: a known-fast Solver body. Call `_execute_submission(body,
  workspace, tasks_dir, dev_hard_wall_sec=10.0)`.
- **Assert**: the inner `score_submission` saw `hard_wall_sec == 10.0`.

Test code:
- [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py)
- [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

