# `test_when_battery_filter_applied_then_skipped_models_excluded`

> Auto-generated stub (cycle 106 backfill). Refine the Arrange / Act /
> Assert sections with prose that could reconstruct the test if the
> code is lost.

## Behaviour

select_battery drops `bench_skip: True` entries; preserves order.

## Contract

- **Arrange**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Act**: (see test body — no `# Arrange/Act/Assert` markers in source)
- **Assert**: (see test body — no `# Arrange/Act/Assert` markers in source)

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

Test code: [`tests/reward_bench/frameworks/test_run_battery.py`](../../../../tests/reward_bench/frameworks/test_run_battery.py)::`test_when_battery_filter_applied_then_skipped_models_excluded`.

## Runtime scope

> **Runtime scope**: unit only — framework orchestration; production-runtime coverage via canonical bench (run_canonical_battery) and @smoke multi-model battery.

