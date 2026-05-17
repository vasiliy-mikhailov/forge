# `test_when_bench_run_with_orchestrator_then_returns_best_scored_submission`

Pins the top-level `bench` composition per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7:

    bench env cfg = argmaxBy (.score) (orchestrate env cfg)

The Python signature takes the `Orchestrator` as an explicit
parameter (Python lacks Haskell's typeclass dispatch). `bench` is
the pure composition of `orchestrate` and `best_submission` — no
IO of its own; whatever IO the orchestrator does is the
orchestrator's.

- **Arrange**: two `Submission` instances `a, b` with `b` higher
  scored. Inline class `FakeOrch` with
  `orchestrate(env, cfg) -> [a, b]`. Construct minimal `Env` and
  default `BenchConfig()`.
- **Act**: `bench(FakeOrch(), env, cfg)`.
- **Assert**: returns `b` (`is b` — the same Submission instance).

Test code: [`../../../../tests/reward_bench/use_cases/test_bench.py`](../../../../tests/reward_bench/use_cases/test_bench.py)::`test_when_bench_run_with_orchestrator_then_returns_best_scored_submission`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — pure composition over an Orchestrator double; no runtime boundary involved.
