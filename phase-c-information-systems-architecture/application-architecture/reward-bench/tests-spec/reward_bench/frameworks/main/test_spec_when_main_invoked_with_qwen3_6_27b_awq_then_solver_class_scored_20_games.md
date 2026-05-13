# `test_when_main_invoked_with_qwen3_6_27b_awq_then_solver_class_scored_20_games`

Pins the **happy-path contract** for the bench end-to-end run: when
`main()` runs against the live `qwen3.6-27b-awq` model, the model
must produce a valid `class Solver` and `score_submission` must play
all 20 canonical seeds. Sentinel `n_games=0` is NOT acceptable for
this cycle — that was the cycle-11 shape-only contract.

- **Arrange**: import `AttemptResult` and `main`. vLLM container
  serving `qwen3.6-27b-awq`.
- **Act**: `result = main(model_id='qwen3.6-27b-awq')`.
- **Assert**:
  - `isinstance(result, AttemptResult)`.
  - `result.n_games == 20` (no sentinel — the model produced a valid
    Solver class).
  - `len(result.games) == 20`.
  - Every game has `final_state in {'won', 'lost'}` (not
    `'solver_error'` or `'invalid_action'`).
  - `result.mean_score >= 0.0`.

Real-system observation from cycle 11: qwen3.6-27b-awq under the
prior `SYSTEM_PROMPT` + `FIRST_USER` consistently produces
`def solve(state)` returning int actions instead of `class Solver`
returning WASD strings. This cycle drives the prompts to convergence
until the test goes green.

Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).
