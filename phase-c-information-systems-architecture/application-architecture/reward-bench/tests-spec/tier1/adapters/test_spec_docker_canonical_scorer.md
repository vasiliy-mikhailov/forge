# `test_spec_docker_canonical_scorer`

Pins the **`DockerCanonicalScorer`** adapter introduced in cycle 105
sub-B per the
[ADR 0006 Layer 2 amendment](../../../../SOLUTION-ARCHITECTURE.md).

## Why

ADR 0006 promised a Docker-isolated canonical scorer; the
infrastructure (Dockerfile.tier1 + tasks/2048/runner_canonical.py) had
existed since cycle 87 but the bench's runtime path still used the
in-process scorer. The 2026-05-16 overnight bench exposed exactly the
failure mode Layer 1 couldn't handle (slow Solver, 2h hang, daemon-thread
can't be force-killed).

[`DockerCanonicalScorer`](../../../../src/tier1/adapters/docker_canonical_scorer.py)
is the host-side adapter that:

- Builds the `docker run` command with the ADR-blessed flags
  (`--rm`, `--network=none`, `--memory=2g`, `--pids-limit=256`,
  `--cpus=N` from the CpuCountPort).
- Mounts the submission, the env module, and the reports directory.
- Threads `REWARD_BENCH_*` env vars from cycle 104 `hard_wall_sec`
  and cycle 78 `stagnation_sec`.
- Reads `/reports/result.json` and maps to `AttemptResult` +
  `GameResult` entities.
- Defensive: missing/unparseable result.json → `walltime_exceeded`
  sentinels for every seed.
- Defensive: subprocess `TimeoutExpired` (outer grace cap) →
  `walltime_exceeded` sentinels.

## Model client injection point

- **Seam**: `DockerCanonicalScorer.__init__(cpu_count_port=...)`.
  Production binds `MultiprocessingCpuCount`; tests inject
  `FixedCpuCount(n)` to assert the `--cpus=N/2` math without
  depending on the host's actual core count.
- **Default**: `fake` — tests use `FixedCpuCount(n)` + monkeypatched
  `subprocess.run` so no real Docker spawn happens.
- **Live override**: production constructs `DockerCanonicalScorer()`
  with the real port. Live tests (cycle 106 candidate) will spawn the
  actual container and assert end-to-end.

## Tests

### `test_when_score_invoked_then_docker_cmd_has_expected_flags`

- **Arrange**: tmp submission.py + env_2048.py; `FixedCpuCount(8)` →
  expected `--cpus=4.0`. Monkeypatch `subprocess.run` to a recorder.
- **Act**: `scorer.score(submission, seeds=(1000, 1001), hard_wall_sec=300)`.
- **Assert**: captured cmd contains `docker`, `run`, `--rm`,
  `--network=none`, `--memory=2g`, `--pids-limit=256`, `--cpus=4.0`,
  the configured image, the three volume mounts, and the
  `REWARD_BENCH_*` env vars.

### `test_when_score_invoked_then_result_json_parsed_into_attempt_result`

- **Arrange**: fake subprocess that writes a 2-game `result.json` to
  the reports mount.
- **Act**: `scorer.score(...)`.
- **Assert**: returned `AttemptResult.n_games == 2`, `mean_score`
  matches the JSON, `games[i].seed/score/max_tile/moves/final_state`
  round-trip correctly.

### `test_when_result_json_missing_then_walltime_exceeded_sentinels`

- **Arrange**: fake subprocess that returns rc=1 without writing
  result.json.
- **Assert**: every seed → `final_state='walltime_exceeded'`,
  `result.walltime_exceeded is True`.

### `test_when_outer_timeout_fires_then_walltime_exceeded_sentinels`

- **Arrange**: fake subprocess raising `subprocess.TimeoutExpired`.
- **Assert**: same sentinel behaviour as missing-result case.

### `test_when_cpus_not_set_then_defaults_to_half_of_cpu_count`

- **Arrange**: `FixedCpuCount(24)`.
- **Assert**: docker cmd contains `--cpus=12.0`.

### `test_when_default_image_then_v04_used`

- **Assert**: `_DEFAULT_IMAGE == 'reward-bench-tier1:0.4'` (matches
  the Dockerfile.tier1 bump in cycle 105 sub-A).

Test code: [`tests/tier1/adapters/test_docker_canonical_scorer.py`](../../../../tests/tier1/adapters/test_docker_canonical_scorer.py).

## Runtime scope

> **Runtime scope**: unit only — tier1 adapter contract; @live coverage at the production-scale boundary per the relevant cycle (123/124/125/128).

