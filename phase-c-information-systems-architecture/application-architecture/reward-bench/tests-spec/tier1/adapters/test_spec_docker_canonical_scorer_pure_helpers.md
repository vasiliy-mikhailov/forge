# `test_spec_docker_canonical_scorer_pure_helpers`

Pins the three pure helpers extracted from `DockerCanonicalScorer.score`:

- `build_docker_cmd(opts) -> tuple[str, ...]` — pure cmd construction.
- `parse_result_payload(payload, seeds) -> tuple[GameResult, ...]` — pure
  runner-JSON → entity mapping.
- `aggregate_attempt(games, elapsed_sec, hard_wall_sec) -> AttemptResult` —
  pure aggregation.

The public `.score()` becomes thin orchestration over these helpers
plus the two I/O steps (subprocess + filesystem read). Each helper is
testable without touching Docker, subprocess, or the filesystem.

This lift instantiates the senior-FP / fitness-function stance:
- **Pure functions** isolate the deterministic core from the imperative
  edges. The cmd-builder and parser become unit-time fitness functions
  for what the production bench actually does.
- **The cmd-builder fitness function in particular** is the regression
  gate for the open bench-bug class (zero-score artifacts from
  bench-spawned docker): if the cmd shape changes silently, the test
  fails before the multi-hour campaign exposes it.

## Tests

### `test_when_build_docker_cmd_called_with_options_then_returns_canonical_arg_tuple`

- **Arrange**: pure inputs only — `image='reward-bench-tier1:0.4'`,
  `submission_path=Path('/tmp/sub.py')`, `env_path=Path('/tmp/env.py')`,
  `reports_dir=Path('/tmp/reports')`, `cpus=4.0`, `memory='2g'`,
  `pids_limit=256`, `stagnation_sec=60`, `hard_wall_sec=300.0`,
  `seed_base=1000`, `n_games=20`.
- **Act**: `cmd = build_docker_cmd(**opts)`.
- **Assert**: `cmd` is a `tuple` (immutable per FP stance). Contains
  in order: `'docker', 'run', '--rm', '--network=none',
  '--memory=2g', '--pids-limit=256', '--cpus=4.0',
  '-v', '/tmp/sub.py:/workspace/submission.py:ro',
  '-v', '/tmp/env.py:/env/env_2048.py:ro',
  '-v', '/tmp/reports:/reports',
  '-e', 'REWARD_BENCH_NUM_GAMES=20',
  '-e', 'REWARD_BENCH_SEED_BASE=1000',
  '-e', 'REWARD_BENCH_STAGNATION_SEC=60',
  '-e', 'REWARD_BENCH_HARD_WALL_SEC=300.0',
  'reward-bench-tier1:0.4'`.
- **Also assert**: `env_path=None` omits the env mount; everything else
  is unchanged.
- **Also assert**: calling the function twice with the same inputs
  returns equal tuples (pure / deterministic).

### `test_when_parse_result_payload_called_with_runner_json_then_returns_game_result_tuple`

- **Arrange**: a payload dict shaped like `/reports/result.json`:
  `{'games': [{'seed': 1000, 'score': 1500, 'max_tile': 128, 'moves': 200,
  'final_state': 'lost', 'walltime_sec': 1.5},
  {'seed': 1001, 'score': 0, 'max_tile': 2, 'moves': 0,
  'final_state': 'solver_error', 'walltime_sec': 0.0}]}`.
  Seeds `(1000, 1001, 1002)`.
- **Act**: `games = parse_result_payload(payload, seeds)`.
- **Assert**: `games` is a tuple of 3 `GameResult` entities, one per
  seed in order. Seeds 1000 and 1001 round-trip from payload. Seed 1002
  (missing from payload) gets a walltime_exceeded sentinel
  (`score=0, max_tile=2, moves=0, final_state='walltime_exceeded',
  walltime_sec=0.0`).
- **Also assert**: passing an empty payload `{'games': []}` with seeds
  `(1000, 1001)` returns two walltime_exceeded sentinels.

### `test_when_aggregate_attempt_called_with_games_then_returns_attempt_result_with_correct_aggregates`

- **Arrange**: tuple of 3 `GameResult` entities with scores
  `(1000, 2000, 3000)`, max_tiles `(128, 256, 512)`, mixed final_states
  including one `'stagnated'` and zero `'walltime_exceeded'`.
  `elapsed_sec=42.0`, `hard_wall_sec=300.0`.
- **Act**: `result = aggregate_attempt(games, elapsed_sec=42.0,
  hard_wall_sec=300.0)`.
- **Assert**: `result.mean_score == 2000.0`, `result.median_score == 2000`,
  `result.max_max_tile == 512`, `result.n_games == 3`,
  `result.aggregate_walltime_sec == 42.0`, `result.hard_wall_sec == 300.0`,
  `result.stagnated_any is True`, `result.walltime_exceeded is False`,
  `result.games is games` (no copy).
- **Also assert**: empty tuple → zero-filled `AttemptResult` with
  `n_games=0`.

Test code: [`tests/tier1/adapters/test_docker_canonical_scorer_pure_helpers.py`](../../../../tests/tier1/adapters/test_docker_canonical_scorer_pure_helpers.py).

## Model client injection point

- **Seam**: none — these are pure functions with no DI surface.
- **Mode**: fake (default) — same as any unit test.

## Runtime scope

> **Runtime scope**: unit only — pure helpers have no runtime
> dependency. Production-runtime coverage of the surrounding
> `DockerCanonicalScorer.score` orchestration is via the existing
> live-runtime test.
