# `test_when_campaign_run_with_iters100_T07_n3_then_artifact_written_with_required_fields`

Pins the leaderboard-data-point contract under
`BenchConfig(max_iters=100, n_trials=3, temperature=0.7,
hard_wall_sec=60)`. The test runs the campaign live against
`qwen3.6-27b-awq`, writes the result to a declared artifact path,
and asserts the artifact's SHAPE (not its specific numeric values —
model noise is real).

This is the test-backed replacement for the deleted ad-hoc
`bin/run_campaign.py`. Per the cats.md
**artifacts-come-from-tests** rule, every leaderboard data point
must come from a pytest test that pins its shape.

`supervisor_every_k=10` was added in cycle 36 — every 10 iters the
bench LLM is asked (via LlmSupervisor) to judge plateau from the
real dev_runner sweep, and the agent loop terminates early on
stop_recommended=True. See ADR 0005.

`hard_wall_sec=60` was added in cycle 26 to bound the per-trial
score_submission walltime (per ADR 0006 layer 1). Without this knob
the cycle-22 attempt hung 34+ minutes on a slow Solver. With it,
each trial is capped at 60 s of aggregate scoring time; remaining
seeds get sentinel `final_state='walltime_exceeded'` per cycle 23.

- **Arrange**: import `main`, `BenchConfig`, `run_bench_trials`,
  `json`. The artifact path is
  `experiments/2026-05-13-iters100-T07-n3.json` (committed alongside
  the test). Config: `BenchConfig(max_iters=100, n_trials=3,
  temperature=0.7, hard_wall_sec=60)`.
- **Act**: run the 3-trial campaign live; write per-trial
  `mean_score`, aggregated `mean_of_means`, `best_mean`,
  `worst_mean`, `max_max_tile`, `aggregate_walltime_sec`, and the
  config metadata into a JSON object at the artifact path.
- **Assert** (shape only — does NOT assert specific scores; model
  noise is real and the test must be re-runnable):
  - The artifact file exists at the declared path.
  - The artifact is valid JSON.
  - Required top-level keys present: `model_id`, `config`,
    `n_trials`, `per_trial_mean`, `mean_of_means`, `best_mean`,
    `worst_mean`, `max_max_tile`, `aggregate_walltime_sec`.
  - `len(per_trial_mean) == 3`.
  - Every numeric field is finite and non-negative.

Pytest marker: `@pytest.mark.campaign` — opt-in via
`pytest -m campaign`; the default TIA per-cycle gate skips this
test because it takes minutes (bounded now by `hard_wall_sec`).

Test code: [`tests/reward_bench/frameworks/campaigns/test_iters100_T07_n3.py`](../../../../tests/reward_bench/frameworks/campaigns/test_iters100_T07_n3.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — @pytest.mark.campaign tests ARE the production runtime — same contract under production-scale config.

