# `test_when_outer_timeout_fires_then_walltime_exceeded_sentinels`

Pins the `subprocess.TimeoutExpired` branch: when the outer grace
cap (`hard_wall_sec + 30s`) fires, `.score()` catches the exception,
treats it as missing result, and returns walltime_exceeded sentinels
for every seed.

## Contract

- **Arrange**: `tmp_path/submission.py` stub; `tmp_path/reports/`.
  Monkeypatch `subprocess.run` to raise
  `subprocess.TimeoutExpired(cmd, timeout=30)`.
- **Act**: `scorer.score(sub, seeds=(1, 2), hard_wall_sec=10.0,
  reports_root=reports)`.
- **Assert**: `result.walltime_exceeded is True`.

## Model client injection point

- **Seam**: `subprocess.run` (monkeypatched to raise).
- **Mode**: fake raises `TimeoutExpired`.
- **Marker**: `@pytest.mark.no_fake`.

Test code: [`../../../../tests/tier1/adapters/test_docker_canonical_scorer.py`](../../../../tests/tier1/adapters/test_docker_canonical_scorer.py)::`test_when_outer_timeout_fires_then_walltime_exceeded_sentinels`.

## Runtime scope

> **Runtime scope**: unit only.
