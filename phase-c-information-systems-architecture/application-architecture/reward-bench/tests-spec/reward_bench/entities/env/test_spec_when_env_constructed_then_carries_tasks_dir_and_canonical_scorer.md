# `test_when_env_constructed_then_carries_tasks_dir_and_canonical_scorer`

Pins the `Env` entity per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7:

    bench :: Env -> BenchConfig -> Submission
    score :: Env -> Submission -> Score

`Env` is the bundle of infrastructure seams both `score` and
`orchestrate` read but `BenchConfig` does not own — the canonical
scorer (how a body becomes a score) and the tasks dir (where the
env's task definition lives). Frozen value object so two
orchestrators run against the *same* Env in dominance comparisons.

- **Arrange**: import `Env`; build a `FakeCanonicalScorer`; pick a
  throwaway `tasks_dir = Path('/tmp/x')`.
- **Act**: construct `Env(tasks_dir=tasks_dir, canonical_scorer=fake)`.
- **Assert**: `env.tasks_dir == tasks_dir` and
  `env.canonical_scorer is fake`.

Test code: [`../../../../tests/reward_bench/entities/test_env.py`](../../../../tests/reward_bench/entities/test_env.py)::`test_when_env_constructed_then_carries_tasks_dir_and_canonical_scorer`.

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — frozen-dataclass invariant; no runtime boundary involved.
