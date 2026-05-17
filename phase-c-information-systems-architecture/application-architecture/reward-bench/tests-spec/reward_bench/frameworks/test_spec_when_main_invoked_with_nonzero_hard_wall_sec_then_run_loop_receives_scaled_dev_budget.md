# `test_when_main_invoked_with_nonzero_hard_wall_sec_then_run_loop_receives_scaled_dev_budget`
## Behaviour
dev_hard_wall_sec = config.hard_wall_sec * 5 / len(seeds)
 and threads it into run_loop. Pins the wiring.
## Contract
- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py)::`test_when_main_invoked_with_nonzero_hard_wall_sec_then_run_loop_receives_scaled_dev_budget`.
## Runtime scope
> **Runtime scope**: unit only — framework orchestration; production-runtime coverage via canonical bench (run_canonical_battery) and @smoke multi-model battery.
