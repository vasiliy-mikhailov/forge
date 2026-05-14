# `test_when_per_model_bench_run_then_canonical_artifact_emitted`

Per-model leaderboard data point for the [model registry](
../../../../src/reward_bench/use_cases/model_registry.py)
(mirrored from [`wiki-compiler/configs/models.yml`](
../../../../../../wiki-compiler/configs/models.yml) per
[SPEC.md](../../../../SPEC.md)).

Per [cats.md artifacts-come-from-tests](
../../../../../../../phase-preliminary/cats.md), each leaderboard
cell (one model x one tier x one config) MUST come from a pytest
test that pins its shape. This test is parameterised over `model_id`
via the `BENCH_MODEL_ID` environment variable so a single test
implementation produces one cell.

The actual agent loop driving the bench is the **blessed runner** per
[ADR 0007](../../../../docs/adr/0007-per-model-bench-uses-blessed-runner-until-agent-loop-bisect.md).
The test records the runner identity in the artifact's `runner` field
but does NOT pin its specific value — so swapping the runner later
(when ADR 0007 is superseded) doesn't churn this test_spec.

- **Arrange**: read `model_id` from environment variable
  `BENCH_MODEL_ID` (caller-supplied, e.g. via
  `BENCH_MODEL_ID=qwen3.5-27b-nvfp4 pytest -m campaign ...`). Verify
  the ID is in `MODEL_REGISTRY`. Verify vLLM is healthy at the served
  name. Workspace = `experiments/2026-05-14-<model_id>-bak-runner-workspace/`.
- **Act**: drive the blessed runner (ADR 0007) end-to-end. Inputs:
  `max-iters=200`, `temperature=0.7`, `seed=1`. Outputs:
  `workspace/submission.py`. Score that submission on canonical seeds
  1000-1019 via `GameBoard2048Adapter.play_one_game`. Write artifact
  at `experiments/2026-05-14-<model_id>-bak-runner.json`.
- **Assert** (shape only — model noise is real; test must be
  re-runnable without asserting absolute scores):
  - Artifact exists, valid JSON.
  - Required keys: `model_id`, `served_name`, `runner`, `seed`,
    `temperature`, `max_iters`, `n_canonical_games`, `scores`,
    `mean`, `median`, `max`, `min`, `max_max_tile`.
  - `n_canonical_games == 20`.
  - `len(scores) == 20`.
  - All numeric fields are finite and non-negative.

Pytest marker: `@pytest.mark.campaign`. Wall time per model:
~2-30 min (depends on how fast the model converges + calls `finish`).
Skips with reason if `BENCH_MODEL_ID` is unset (default state — keeps
the per-cycle TIA gate fast).

Test code: [`tests/reward_bench/frameworks/campaigns/test_per_model_bak_runner.py`](../../../../tests/reward_bench/frameworks/campaigns/test_per_model_bak_runner.py).
