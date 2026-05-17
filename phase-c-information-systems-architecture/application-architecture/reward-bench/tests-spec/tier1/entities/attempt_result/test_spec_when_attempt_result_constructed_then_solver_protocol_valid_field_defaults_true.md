# `test_when_attempt_result_constructed_then_solver_protocol_valid_field_defaults_true`
Adds `solver_protocol_valid: bool = True` to
[`AttemptResult`](../../../../src/tier1/entities/attempt_result.py).
Default True preserves behaviour for tests that don't opt in;
`main()` sets it to False when
[`validate_submission_protocol`](../../../../src/tier1/harness.py)
returns violations, surfacing the contract failure into the artifact
alongside the existing `walltime_exceeded` / `stagnated_any` flags.
- **Arrange**: import `AttemptResult`.
- **Act**: construct with defaults; then with `solver_protocol_valid=False`.
- **Assert**: default is `True`; explicit `False` is preserved.
Test code: [`tests/tier1/entities/test_attempt_result.py`](../../../../tests/tier1/entities/test_attempt_result.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.
