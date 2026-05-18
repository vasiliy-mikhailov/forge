# `test_when_openhands_solution_generator_generate_called_with_snapshot_time_then_runner_receives_that_deadline`

Per [`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4 time budget contract: `snapshot.time_remaining_sec` is a
binding deadline — the SolutionGenerator adapter must hand it
through to the runner closure. The runner wraps the container
spawn in `timeout N docker run …`, so the value must flow
unmodified from snapshot to subprocess command line.

- **Arrange**: a stub `_openhands_runner` that records its
  `deadline_sec` argument; a `ContextSnapshot` with
  `time_remaining_sec=42.5`.
- **Act**: `adapter.generate(snap)`.
- **Assert**: the captured `deadline_sec == 42.5`.

Test code: [`../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py`](../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py)::`test_when_openhands_solution_generator_generate_called_with_snapshot_time_then_runner_receives_that_deadline`.

## Model client injection point

- **Seam**: stub `_openhands_runner` callable with 2-arg signature.
- **Mode**: **fake** — no SDK, no docker.

## Runtime scope

> **Runtime scope**: unit only — pure argument-passthrough.
