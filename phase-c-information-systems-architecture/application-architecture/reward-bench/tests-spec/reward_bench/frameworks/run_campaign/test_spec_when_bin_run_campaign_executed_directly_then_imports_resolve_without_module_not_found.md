# `test_when_bin_run_campaign_executed_directly_then_imports_resolve_without_module_not_found`

Pins that the campaign entry point `bin/run_campaign.py` is
runnable from the repo root with `python3 bin/run_campaign.py` —
i.e., its top-level imports resolve without `ModuleNotFoundError`.

When Python executes a script directly via
`python3 bin/run_campaign.py`, it sets `sys.path[0]` to the script's
directory (`bin/`) — NOT the repo root. So `from src.* import ...`
fails because `src/` is not on `sys.path`. This is the bug surfaced
when the cycle-22 live campaign run crashed instantly with
`ModuleNotFoundError: No module named 'src'`.

Per the cats.md no-silent-fix rule (added in commit 23ba781), this
test pins the bug as a behaviour contract so the regression is
never free to come back.

The script accepts a `--check` flag (cycle 22.5 minimum-impl
addition) that exits 0 after imports resolve without running the
real bench (which would take 10+ minutes). The test runs the
script with `--check` in a subprocess from the repo root and
asserts exit code 0.

- **Arrange**: locate the repo-root path (`bench/`) and
  `bin/run_campaign.py`. Build the subprocess argv list
  `[sys.executable, 'bin/run_campaign.py', '--check']`. cwd is the
  repo root.
- **Act**: run the subprocess; capture exit code, stdout, stderr.
- **Assert**:
  - `returncode == 0` — script ran to completion without errors.
  - `'ModuleNotFoundError' not in stderr` — explicit pin against
    the original failure mode.
  - `'imports OK' in stdout` — the check-mode sentinel printed by
    the script.

Test code: [`tests/reward_bench/frameworks/test_run_campaign.py`](../../../../tests/reward_bench/frameworks/test_run_campaign.py).
