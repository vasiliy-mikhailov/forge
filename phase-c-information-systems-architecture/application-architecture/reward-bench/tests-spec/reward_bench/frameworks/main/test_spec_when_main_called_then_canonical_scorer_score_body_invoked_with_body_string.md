# `test_when_main_called_then_canonical_scorer_score_body_invoked_with_body_string`

Pins the §7.5 migration of `main.py`'s canonical-scoring step per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7.5. The final canonical-scoring call now uses
`canonical_scorer.score_body(body=..., ...)` — body string read
from `workspace/submission.py` and passed in-memory.

`reports_root` is dropped: it was a caller-chosen path for per-game
event logs, never read back by main.py. Removing it eliminates the
last path-shaped scorer argument and unblocks subsequent
"drop .score(submission_path, ...)" cycle.

- **Arrange**: a recording `FakeCanonicalScorer` capturing
  `score_body` kwargs; minimal `BenchConfig(max_iters=1)`; the
  test pre-writes `workspace/submission.py` so the existing
  `submission_path.read_text()` path works through agent loop
  setup. Injected `model_client` returns a finish reply
  immediately.
- **Act**: `main(model_id='...', config=cfg,
  canonical_scorer=fake_scorer, ...)`.
- **Assert**: the fake's `score_body` was called with the body
  text from the pre-written submission file.

Test code: [`../../../../tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py)::`test_when_main_called_then_canonical_scorer_score_body_invoked_with_body_string`.

## Model client injection point

- **Seam**: `canonical_scorer=` parameter on `main()`.
- **Mode**: **fake** — recording scorer.

## Runtime scope

> **Runtime scope**: unit only — fakes for both model_client and canonical_scorer; no Docker, no vLLM.
