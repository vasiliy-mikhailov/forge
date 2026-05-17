# `src_spec_agent_loop_helpers_pure_state_machine`

[`../../../src/tier1/agent_loop_helpers.py`](../../../src/tier1/agent_loop_helpers.py) — pure helpers extracted from `run_loop`'s in-loop state machine. Five functions, all side-effect-free:

- `reject_finish_for_floor(finish_floor, best_dev_mean) -> str | None`
- `update_best_snapshot(current_best, new_mean) -> (new_best, snapshot_fires)`
- `sweep_sample(iter_n, parsed) -> (iter_n, mean, max_tile, walltime)`
- `should_smoke_stop(smoke_early_stop, best_dev_mean) -> bool`
- `promote_body_text(body) -> str`

Each is a pure transition over the loop's progress state — no I/O,
no time, no globals. The orchestrator (`run_loop`) wires them
together with the impure edges (model call, tool dispatch, file
write). Per the Haskell stance: imperative orchestration becomes
thin glue over pure decisions.

## Contracts

See test_spec_agent_loop_pure_helpers.md in tests-spec/tier1/agent_loop/
for behaviour pins, and the test file for executable contracts.
