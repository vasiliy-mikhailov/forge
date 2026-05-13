# `test_when_solver_class_instantiated_then_exposes_callable_move`

Pins submission layer L5.2: the Solver class can be instantiated
with no args and exposes a callable `move` attribute.

- **Arrange**: skill_tier1_reply → extract_python → temp file →
  load_submission → module.Solver.
- **Act**: `Solver()` → instance; getattr `move`.
- **Assert**: instance is a Solver, `move` is callable.

Test code: [`tests/tier1/test_harness.py`](../../tests/tier1/test_harness.py).
