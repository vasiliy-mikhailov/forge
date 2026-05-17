# `test_when_submission_source_lacks_transitions_import_then_violation`
Pins the **transitions soft-grep enforcement** in
[`validate_submission_protocol`](../../../../src/tier1/harness.py)
per [SPEC.md §Tier 1](../../../../SPEC.md):
> The class MUST use the `transitions` library to declare states +
> transitions (we grep for `from transitions import` and reject
> otherwise — soft enforcement).
added Solver/move protocol validation; closes the
SPEC promise of `transitions` enforcement.
Mechanism: `validate_submission_protocol(module, source: str | None = None)`.
When `source` is provided AND `'from transitions import'` is NOT a
substring of `source`, the returned violations tuple includes a
human-readable entry naming the missing transitions import. When
`source` is None, the check is skipped (back-compat for callers
that don't yet pass the body — primarily older tests). The
cycle-58 [`_execute_submission`](../../../../src/tier1/agent_loop.py)
dispatcher and `main()` post-finish path both pass `source`.
"Soft" refers to the grep depth: we don't verify the imported
`Machine` is actually used. A submission that imports transitions
but uses none of it passes the grep. A deeper check is out of
scope.
- **Arrange**: a body with a valid `class Solver` + `move()` but no
 `from transitions import` line at all.
- **Act**:
 ```python
 module = load_submission(path)
 violations = validate_submission_protocol(module, source=body)
 ```
- **Assert**:
 - `violations` is non-empty.
 - One entry mentions `'transitions'` and `'import'`.
Negative-control: body that opens with `from transitions import Machine`
yields no `transitions`-related violation (other validation rules
still apply).
Test code: [`tests/tier1/test_harness.py`](../../../../tests/tier1/test_harness.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — validator AST + grep + class-existence; pure-Python checks; scale-invariant.
