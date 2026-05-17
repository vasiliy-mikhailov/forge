# `test_when_canonical_eval_replayed_then_mean_score_matches_exactly`
Pins Stage 3 replay determinism: per SPEC.md Tier 1 "Replay tolerance:
0% — exact match required". Running `run_canonical_eval` twice on the
same submission produces identical aggregate scores.
- **Arrange**: load `tasks/2048/baselines/reference_fsm.py` twice
 independently.
- **Act**: `run_canonical_eval(Solver)` twice.
- **Assert**: `mean_score`, `median_score`, `max_max_tile` match
 exactly between the two runs.
Test code: [`tests/tier1/test_scorer.py`](../../tests/tier1/test_scorer.py).
## Model client injection point
- **Seam**: conftest autouse `_bind_model_client`.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.
## Runtime scope
> **Runtime scope**: unit only — AttemptResult shape / replay-equality contract; pure-Python; scale-invariant.
