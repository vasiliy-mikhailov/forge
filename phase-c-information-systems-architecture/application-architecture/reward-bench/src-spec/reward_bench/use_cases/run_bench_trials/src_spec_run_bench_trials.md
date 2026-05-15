# `src/reward_bench/use_cases/run_bench_trials.py`

`run_bench_trials` is the multi-trial use case: it invokes a
single-run `runner` (default: `main`) `config.n_trials` times and
returns the resulting `AttemptResult`s as a tuple. This is the
multi-trial driver layer for the
[ADR 0003](../../../../docs/adr/0003-bench-defaults-500-iters-10-trials-temp-0.7.md)
`n_trials=10` campaign default.

## Function

    def run_bench_trials(
        model_id: str,
        config: BenchConfig,
        runner: Callable[..., AttemptResult],
    ) -> tuple[AttemptResult, ...]

## Behavior

For `i in range(config.n_trials)` invokes
`runner(model_id=model_id, config=config)` and collects the result.
Returns the collected results as a tuple.

Note: `runner` has no default to keep the use case layer-pure (use_cases cannot import frameworks where main lives). The wiring layer passes `main` explicitly.

The use case is intentionally thin: aggregation (mean of means,
best-of-N, standard deviation) is a separate concern handled by a
presenter / future cycle.

## Layer purity

`use_cases/` imports `entities/` and other `use_cases/` only. The
`runner` parameter's default value (`main`) lives in
`frameworks/`, so the import is at the boundary of the function
signature. Tests pass an explicit stub runner so the use case
remains layer-pure.
