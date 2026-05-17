# `test_when_cpus_not_set_then_defaults_to_half_of_cpu_count`

Pins the constructor default for `cpus`: when not passed,
`DockerCanonicalScorer` uses `cpu_count_port.cpu_count() / 2`. The
resulting `--cpus=N/2` flag must appear in the docker cmd.

## Contract

- **Arrange**: `tmp_path/submission.py` stub; `tmp_path/reports/`.
  Construct `scorer = DockerCanonicalScorer(cpu_count_port=
  FixedCpuCount(24))` — no explicit `cpus` arg. Monkeypatch
  `subprocess.run` with the recorder fake.
- **Act**: `scorer.score(sub, seeds=(1, 2), hard_wall_sec=10.0,
  reports_root=reports)`.
- **Assert**: `'--cpus=12.0' in captured['cmd']` (24 / 2 = 12.0).

## Model client injection point

- **Seam**: `CpuCountPort` via constructor injection
  (`FixedCpuCount(24)`); `subprocess.run` monkeypatched as recorder.
- **Mode**: fake throughout.
- **Marker**: `@pytest.mark.no_fake`.

Test code: [`../../../../tests/tier1/adapters/test_docker_canonical_scorer.py`](../../../../tests/tier1/adapters/test_docker_canonical_scorer.py)::`test_when_cpus_not_set_then_defaults_to_half_of_cpu_count`.

## Runtime scope

> **Runtime scope**: unit only.
