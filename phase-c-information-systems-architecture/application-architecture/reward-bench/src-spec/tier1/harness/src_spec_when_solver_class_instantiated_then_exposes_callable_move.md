# `src_spec_when_solver_class_instantiated_then_exposes_callable_move`
The Solver class declared by the submission MUST be instantiable
with no positional arguments (`Solver()`), and the instance MUST
expose an attribute `move` that is callable. This is the contract
the harness depends on before invoking `solver.move(board)` per
SPEC.md Tier 1 submission protocol.
No bench-side code change — this layer is satisfied by the
submission itself. The harness only asserts the contract.
