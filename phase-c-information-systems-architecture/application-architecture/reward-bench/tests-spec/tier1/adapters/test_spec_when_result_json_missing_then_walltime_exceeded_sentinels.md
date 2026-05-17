# `test_when_result_json_missing_then_walltime_exceeded_sentinels`

Pins the defensive branch: when the container exits without writing
`/reports/result.json`, every seed gets a `walltime_exceeded`
sentinel rather than `.score()` raising. Triggers the diagnostic
log (cmd + returncode + stdout/stderr tails + reports_dir contents)
so the silent failure is self-explaining.

## Contract

- **Arrange**: `tmp_path/submission.py` stub; `tmp_path/reports/`.
  Monkeypatch `subprocess.run` with a fake that returns
  `CompletedProcess(returncode=1, stdout='', stderr='crash')` and
  does **not** write `result.json`.
- **Act**: `scorer.score(sub, seeds=(1, 2, 3), hard_wall_sec=300.0,
  reports_root=reports)`.
- **Assert**: `result.n_games == 3`; every
  `g.final_state == 'walltime_exceeded'`;
  `result.walltime_exceeded is True`.

## Model client injection point

- **Seam**: `subprocess.run` (monkeypatched).
- **Mode**: fake returns non-zero exit without writing result.json.
- **Marker**: `@pytest.mark.no_fake`.

Test code: [`../../../../tests/tier1/adapters/test_docker_canonical_scorer.py`](../../../../tests/tier1/adapters/test_docker_canonical_scorer.py)::`test_when_result_json_missing_then_walltime_exceeded_sentinels`.

## Runtime scope

> **Runtime scope**: unit only.
