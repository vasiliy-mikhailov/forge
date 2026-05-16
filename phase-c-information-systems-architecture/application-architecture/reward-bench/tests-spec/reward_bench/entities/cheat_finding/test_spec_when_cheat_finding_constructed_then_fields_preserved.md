# `test_when_cheat_finding_constructed_then_fields_preserved`

Pins the `CheatFinding` data contract from SPEC.md pydantic schema —
one row in the anti-cheat report. Anti-cheat is an orchestrator
concern, so the entity lives in `src/reward_bench/entities/`.

- **Arrange**: import `CheatFinding`.
- **Act**: construct `CheatFinding(layer='ast', severity='rejected',
  rule='no_subprocess', line=12, code='import subprocess')`.
- **Assert**: every field reads back its constructor value; frozen
  dataclass.

Test code: [`tests/reward_bench/entities/test_cheat_finding.py`](../../../../tests/reward_bench/entities/test_cheat_finding.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

