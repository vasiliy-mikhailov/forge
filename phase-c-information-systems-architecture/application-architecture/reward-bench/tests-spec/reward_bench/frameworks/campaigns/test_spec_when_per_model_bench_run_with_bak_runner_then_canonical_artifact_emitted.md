# `test_when_per_model_bench_run_with_bak_runner_then_canonical_artifact_emitted`

Per-model leaderboard data point for the spec.md model registry.
Uses [`_bak/bin/agent_loop.py`](../../../../_bak/bin/agent_loop.py)
as the BLESSED runner pending [cycle 41+ bisect of the regression in
`src/tier1/agent_loop.py`](../../../../experiments/leaderboard_data.md#cycle-40-reproduction).

Why _bak's loop and not ours: cycle 40 ran _bak/bin/agent_loop.py
unmodified against the same vLLM endpoint and reproduced qwen3.6-27b-awq
mean=11734 (matching _bak's 2026-05-05 baseline of 10884). Our
src/tier1/agent_loop.py on the same model peaked at 6525 — a ~40
percent regression. Until that regression is bisected, _bak's loop is
the reproducible reference for per-model data points.

Per cats.md artifacts-come-from-tests: each leaderboard cell (one
model x one tier x one config) MUST come from a pytest test that
pins its shape. This test is parameterised over `model_id` so a single
test produces one cell.

- **Arrange**: read `model_id` from environment variable
  `BENCH_MODEL_ID` (caller-supplied, e.g. via
  `BENCH_MODEL_ID=qwen3.6-27b-awq pytest -m campaign ...`). Verify the
  ID is in `MODEL_REGISTRY`. Verify vLLM is healthy at the served name.
  Workspace = `experiments/2026-05-14-<model_id>-bak-runner-workspace/`.
- **Act**: subprocess-launch `_bak/bin/agent_loop.py` with
  `--max-iters 200 --max-no-improve 999999 --finish-floor 0
  --max-wall-sec 7200 --seed 1 --temperature 0.7
  --context-budget-tokens 100000`. Wait for it to write
  `workspace/submission.py`. Score that submission on canonical seeds
  1000-1019 via `GameBoard2048Adapter.play_one_game`. Write artifact at
  `experiments/2026-05-14-<model_id>-bak-runner.json`.
- **Assert** (shape only):
  - Artifact exists, valid JSON.
  - Required keys: `model_id`, `served_name`, `runner`, `seed`,
    `temperature`, `max_iters`, `n_canonical_games`, `scores`,
    `mean`, `median`, `max`, `min`, `max_max_tile`.
  - `runner == '_bak/bin/agent_loop.py'`.
  - `n_canonical_games == 20`.
  - `len(scores) == 20`.
  - All numeric fields are finite and non-negative.

Pytest marker: `@pytest.mark.campaign`. Wall time per model: ~10-30 min.

Skips with reason if `BENCH_MODEL_ID` is unset (default state).

Test code: [`tests/reward_bench/frameworks/campaigns/test_per_model_bak_runner.py`](../../../../tests/reward_bench/frameworks/campaigns/test_per_model_bak_runner.py).
