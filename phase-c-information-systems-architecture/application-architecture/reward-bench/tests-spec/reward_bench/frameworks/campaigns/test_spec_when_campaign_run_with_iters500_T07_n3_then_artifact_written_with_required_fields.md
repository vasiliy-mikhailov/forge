# `test_when_campaign_run_with_iters500_T07_n3_then_artifact_written_with_required_fields`

Cycle 37 leaderboard data point under `BenchConfig(max_iters=500,
n_trials=3, temperature=0.7, hard_wall_sec=120,
supervisor_every_k=20)`. Chases [`_bak`'s 15920](
../../../../experiments/leaderboard_data.md#bak-legacy-campaign-2026-04-archived)
which used `max_iters=500 n_trials=10` — we keep n_trials=3 in this
cycle to bound wall time (10 trials at this budget = ~10 hours).

`supervisor_every_k=20` (not 10) at this budget — with 500 iters per
trial, consulting every 10 iters means 50 supervisor turns per trial,
each ~3-5s. Every 20 cuts that to 25 turns while still letting
plateau detection fire mid-trial.

`hard_wall_sec=120` doubles cycle 36's 60s — at 500 iters the model
may have written a more elaborate Solver that takes longer to score.

Test shape contract is IDENTICAL to the iters100 sibling — only the
config knobs differ. Per cats.md artifacts-come-from-tests, the
leaderboard data point comes from this test.

- **Arrange**: import `main`, `BenchConfig`, `run_bench_trials`, `json`.
  Artifact path: `experiments/2026-05-14-iters500-T07-n3.json`.
- **Act**: run the 3-trial campaign live; write per-trial `mean_score`,
  aggregated metrics into JSON.
- **Assert** (shape only — does NOT assert specific scores):
  - Artifact exists, valid JSON.
  - Required top-level keys: `model_id`, `config`, `n_trials`,
    `per_trial_mean`, `mean_of_means`, `best_mean`, `worst_mean`,
    `max_max_tile`, `aggregate_walltime_sec`.
  - `len(per_trial_mean) == 3`.
  - Every numeric field is finite and non-negative.

Pytest marker: `@pytest.mark.campaign`. Wall time budget: ~60-90 min.

Test code: [`tests/reward_bench/frameworks/campaigns/test_iters500_T07_n3.py`](../../../../tests/reward_bench/frameworks/campaigns/test_iters500_T07_n3.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

