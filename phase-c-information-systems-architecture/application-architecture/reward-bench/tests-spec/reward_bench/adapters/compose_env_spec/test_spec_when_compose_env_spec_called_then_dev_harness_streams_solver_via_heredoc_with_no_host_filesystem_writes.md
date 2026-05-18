# `test_when_compose_env_spec_called_then_dev_harness_streams_solver_via_heredoc_with_no_host_filesystem_writes`

Per [`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§5 ("no file APIs above the Runner"): the dev harness must not
mount a host-side `submission.py`. The Solver source flows via
heredoc → docker stdin → `cat > /workspace/submission.py` inside
the container, where `/workspace` is ephemeral and nothing
crosses to the host filesystem.

`env.py` is mounted read-only — that's the task runtime
configuration baked into the image, not bench↔agent
communication, so it stays.

- **Arrange**: explicit
  `env_py_path=Path('/abs/tasks/2048/env.py')`,
  `tier1_image='reward-bench-tier1:0.4'`, `dev_games=5`,
  `dev_seed_base=2000`, `dev_timeout_sec=60`.
- **Act**: `compose_env_spec(...)`.
- **Assert**:
  - positive: `docker run`, `-i` flag, `<<'SOLVER_END'` heredoc,
    `cat > /workspace/submission.py` inside, env.py read-only
    mount with abs path, image tag, env vars
    (`REWARD_BENCH_NUM_GAMES=5`, `REWARD_BENCH_SEED_BASE=2000`),
    `timeout 60` prefix.
  - negative: NO `:/workspace/submission.py` mount, NO
    `/tmp/sub.py` reference — those would be host-side file
    writes.

Test code: [`../../../../tests/reward_bench/adapters/test_compose_env_spec.py`](../../../../tests/reward_bench/adapters/test_compose_env_spec.py)::`test_when_compose_env_spec_called_then_dev_harness_streams_solver_via_heredoc_with_no_host_filesystem_writes`.

## Model client injection point

None — pure string composer.

## Runtime scope

> **Runtime scope**: unit only — pure function.
