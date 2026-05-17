# `test_when_run_loop_completes_then_no_generated_submission_is_judged_trivial_by_model`

Live fitness function that uses the model-under-test as the judge:
after `run_loop` completes, the final `workspace/submission.py` is
shown to the model with a binary-verdict prompt; the test asserts the
model judges the submission **NON-TRIVIAL**.

Rationale: detecting "trivial" mechanically in Python is hard — a
solver returning constant `'W'` is clearly trivial, but so is `return
board[0][0] % 4 == 0 and 'W' or 'A'` (looks-like-strategy but
isn't). The cleanest detector is the model itself, asked to read the
Solver and report whether it has actual strategy that uses board
state to choose its move.

This test pins the broader sparse-reward / W-fallback drift discussed
in the SOLUTION-ARCHITECTURE §"Open items": even when canonical
scoring passes (cycle-48 best-snapshot restore catches a real solver
early in the run), the model's *final* submission often drifts to
trivial. The test forces visibility on that drift.

## Contract

- **Arrange**: live `vllm_base_url` + `vllm_api_key`. Tmp workspace.
  `_FAST` config (max_iters=120, T=0.7, hard_wall_sec=60). The
  `VllmOpenAIClient` for the judge call.
- **Act**:
  1. Run `main(model_id='qwen3.6-27b-awq', config=_FAST)`.
  2. Read the resulting `workspace/submission.py` (post best-snapshot
     restore).
  3. Send the body to the model with `JUDGE_PROMPT`:

         You are a code reviewer. Below is a Python Solver class for
         the 2048 puzzle. Decide: does this Solver have any actual
         strategy that uses board state (the 4×4 grid) to choose its
         move?

         Reply on a single line with exactly one of these two words:
         TRIVIAL — if the move() method always returns the same
         action, picks randomly without using board, or has no logic
         that inspects board values.
         NON-TRIVIAL — if move() uses board state in a way that
         changes its output based on the grid contents.

         ```python
         {submission_body}
         ```
  4. Parse the model's reply; extract the first occurrence of
     `TRIVIAL` or `NON-TRIVIAL`.
- **Assert**: verdict is `NON-TRIVIAL`. On failure, the test prints
  the submission body and the judge's reply for diagnostic.

## Model client injection point

- **Seam**: live `VllmOpenAIClient` against the lab vLLM container.
- **Mode**: live — judges the actual model-under-test's output with
  itself. Marker `@pytest.mark.live`.

Test code: [`../../tests/tier1/test_trivial_drift.py`](../../tests/tier1/test_trivial_drift.py)::`test_when_run_loop_completes_then_no_generated_submission_is_judged_trivial_by_model`.

## Runtime scope

> **Runtime scope**: live — requires real model under test.
> Production-runtime equivalent is the leaderboard's empirical
> observation of W-fallback rates across the model registry.
