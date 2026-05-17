# `test_when_submission_validated_then_returns_violations_for_missing_solver_or_wrong_move_signature`
Pins the **submission protocol** that
[`tasks/2048/SKILL_tier1.md`](../../../../tasks/2048/SKILL_tier1.md)
declares as required. Until this cycle the contract was enforced
implicitly: `load_submission` ran the module, and `score_submission`
later raised `AttributeError` when `Solver` or `move` were missing —
caught by [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
sentinel as `final_state='solver_error'`. Result: shape-only campaign
tests cannot distinguish "model wrote Gym-style API" from "Solver
crashed during play".
lifts the contract out of the catch-all sentinel into a
named validator:
 `validate_submission_protocol(module) -> tuple[str,...]`
returning a tuple of violation strings (empty tuple = valid). The
contract is:
1. `module.Solver` must exist (a class).
2. `module.Solver` must define a `move` method.
3. `Solver()` constructible without args.
4. `Solver().move(board)` returns a `str` that is one of
 `'W', 'A', 'S', 'D'`, where `board` is a 4x4 list of zeros.
When the campaign artifact records a `final_state` for a sentinel,
the validator's first violation (if any) can be carried alongside so
the leaderboard distinguishes API-shape failures from runtime crashes.
- **Arrange**: build three submission strings:
 - **valid**: `class Solver: def move(self, board): return 'W'`
 - **gym_style**: `def solve(grid): return 0` (no Solver class)
 - **wrong_return**: `class Solver: def move(self, board): return 0`
 Write each to a tmp file, `load_submission`, call validator.
- **Act/Assert**:
 - Valid → returns `()`.
 - Gym-style → first violation contains `'Solver'`.
 - Wrong-return → violations contain `'move()'` or `'W/A/S/D'`.
Test code: [`tests/tier1/test_harness.py`](../../../../tests/tier1/test_harness.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — validator AST + grep + class-existence; pure-Python checks; scale-invariant.
