# `bin/run_campaign.py`

CLI campaign driver. Invokes `run_bench_trials` against
`qwen3.6-27b-awq` with heavier-than-test `BenchConfig` (max_iters,
n_trials, temperature per ADR 0003).

## Invocation modes

- `python3 bin/run_campaign.py` — run the full campaign. Walltime
  10-15 min for `n_trials=3 max_iters=100`.
- `python3 bin/run_campaign.py --check` — verify imports resolve;
  exit 0. Used by the regression test
  `test_when_bin_run_campaign_executed_directly_then_imports_resolve_without_module_not_found`
  to pin the no-silent-fix discipline for this script.

## sys.path bootstrap

When Python runs a script directly, it sets `sys.path[0]` to the
script's parent directory, not the project root. The script
prepends the repo root (`Path(__file__).resolve().parents[1]`) to
`sys.path` BEFORE any `from src.* import ...` so the imports
resolve regardless of cwd. Without this bootstrap the script fails
with `ModuleNotFoundError: No module named 'src'`.
