# `test_when_game_result_constructed_with_each_final_state_literal_then_accepted`
Pins the enumerated `FinalState` from SPEC.md: every one of the seven
literals is a valid `final_state` value.
- **Arrange**: import `GameResult`.
- **Act**: for each of the seven `FinalState` literals, construct a
 `GameResult` with that value (other fields fixed at trivial
 defaults).
- **Assert**: every construction succeeds and `final_state` reads
 back the literal passed in.
The test pins parity with SPEC.md's `FinalState` enumeration. Adding
or removing a final-state literal in SPEC.md without updating
`GameResult.FinalState` will fail this test.
Test code: [`tests/tier1/entities/test_game_result.py`](../../../../tests/tier1/entities/test_game_result.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — frozen-dataclass invariant; asserts on entity shape, no runtime boundary involved.

Test code: [`../../../../tests/tier1/entities/test_game_result.py`](../../../../tests/tier1/entities/test_game_result.py)::`test_when_game_result_constructed_with_each_final_state_literal_then_accepted`.
