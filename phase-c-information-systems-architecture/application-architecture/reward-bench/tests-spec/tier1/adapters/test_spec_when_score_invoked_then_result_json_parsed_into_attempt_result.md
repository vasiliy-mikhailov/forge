# `test_when_score_invoked_then_result_json_parsed_into_attempt_result`
Pins the happy-path orchestration of `DockerCanonicalScorer.score()`:
a fake subprocess writes a 2-game `result.json` to the reports mount;
`.score()` parses it via the pure `parse_result_payload` helper and
aggregates via `aggregate_attempt`. The pure helpers' shape contracts
live in `test_spec_docker_canonical_scorer_pure_helpers`; this test
pins the orchestration path end-to-end.
## Contract
- **Arrange**: `tmp_path/submission.py` with stub `class Solver:...`;
 `tmp_path/reports/` directory; `FixedCpuCount(24)`. Monkeypatch
 `subprocess.run` with a fake that locates the `:/reports` mount in
 the cmd and writes a 2-game payload (`seed=1000 score=1000
 max_tile=64 final_state='lost'`, `seed=1001 score=500 max_tile=32
 final_state='lost'`).
- **Act**: `scorer.score(sub, seeds=(1000, 1001), hard_wall_sec=300.0,
 reports_root=reports)`.
- **Assert**: `result.n_games == 2`; `result.mean_score == 750.0`;
 `result.max_max_tile == 64`; each `result.games[i]` round-trips
 `seed`, `score`, `max_tile` from the payload.
## Model client injection point
- **Seam**: `subprocess.run` (monkeypatched per-test).
- **Mode**: fake recorder writes synthetic `result.json`. Marker
 `@pytest.mark.no_fake` bypasses the autouse fakes; this test
 exercises real `DockerCanonicalScorer` code.
Test code: [`../../../../tests/tier1/adapters/test_docker_canonical_scorer.py`](../../../../tests/tier1/adapters/test_docker_canonical_scorer.py)::`test_when_score_invoked_then_result_json_parsed_into_attempt_result`.
## Runtime scope
> **Runtime scope**: unit only — `subprocess.run` faked. Live coverage
> at `test_docker_canonical_scorer_live.py`.
