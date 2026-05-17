# `src_spec_when_run_loop_produces_submission_then_solver_move_returns_one_of_wasd`
No new code in `src/`. This is the end-to-end assertion of the
existing pipeline:
 run_loop → /workspace/submission.py → load_submission →
 Solver() → solver.move(board) → one of W, A, S, D.
If the test goes red, the failure mode tells us which seam broke:
- `submission.py` missing → the model never emitted a successful `execute_submission`
 call within the budget.
- Submission loads but `Solver` missing or constructor raises → the
 model wrote a syntactically valid module that doesn't satisfy the
 Tier 1 class contract.
- `solver.move(board)` raises → the submission has a runtime bug on
 even the starting board (the same class of failure the static L6.1
 exposed; expected if the model didn't iterate via dev_runner).
- `solver.move(board)` returns non-WASD → contract violation.
The bounded budget (`max_iters=20`) is operational, not normative. If
the test catches the model not converging within the budget, raising
the cap is the cheapest fix.
