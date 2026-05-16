# `test_when_run_loop_produces_submission_then_solver_move_returns_one_of_wasd`

Pins end-to-end interactive Tier 1 down to one usable swipe: after
`run_loop` runs (bounded budget), the workspace contains a
`submission.py` whose `Solver().move(board)` returns one of `W`, `A`,
`S`, `D` on a starting 2048 board. This is the smallest assertion that
the bench's interactive protocol produced a viable Tier 1 submission.

- **Arrange**: `tmp_path` workspace; `tasks_dir`, `env_dir`; live vllm
  fixtures; `max_iters=20`.
- **Act**: `run_loop(...)` runs the model through view → write → bash
  → ... up to the budget. Then load `submission.py` via
  `src.tier1.harness.load_submission`, instantiate `Solver()`, call
  `solver.move(starting_board)`.
- **Assert**: the move return value is in `{W, A, S, D}`. The test
  does NOT require the model to call `finish` — per SPEC.md the file
  at workspace at loop end is what gets scored.

If `submission.py` is missing after the loop, the test fails with that
exact assertion (catching the case where the model never wrote a
file). If `submission.py` exists but the solver raises or returns a
non-WASD value, that's also the failure path — directly the L6.1
contract we reframed earlier, now on a real interactively-iterated
submission instead of a one-shot static reply.

Test code: [`tests/tier1/test_agent_loop.py`](../../tests/tier1/test_agent_loop.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

