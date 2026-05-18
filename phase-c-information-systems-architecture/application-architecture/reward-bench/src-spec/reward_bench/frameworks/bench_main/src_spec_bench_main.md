# `src_spec_bench_main`

[`../../../../src/reward_bench/frameworks/bench_main.py`](../../../../src/reward_bench/frameworks/bench_main.py)
is the §7 production binding per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).
Composes the production `Env` (Docker scorer + VllmOpenAIClient +
repo tasks dir) with `OrchestrateRalphSingleContext` and calls
`bench(orchestrator, env, cfg)`.

Signature:

```python
def bench_main(
    target: ModelTarget,
    cfg: BenchConfig,
    *,
    env_factory: Callable[[ModelTarget], Env] | None = None,
    orchestrator_factory: Callable[[], Orchestrator] | None = None,
) -> Submission: ...
```

Both factories are injectable to keep the function unit-testable
without spawning Docker or vLLM. Defaults:

- `_default_env_factory(target)` calls
  `ensure_serving_model(target)`, reads `VLLM_API_KEY` from env,
  and constructs `Env(tasks_dir=<repo>/tasks,
  canonical_scorer=DockerCanonicalScorer(),
  model_client=VllmOpenAIClient(...))`.
- `_default_orchestrator_factory()` returns
  `OrchestrateRalphSingleContext(run_loop_fn=default_run_loop_fn())`.

Includes a `_cli()` argparse wrapper for direct invocation via
`python -m src.reward_bench.frameworks.bench_main --model-id ...`.
The CLI prints a JSON summary (model_id, wallclock_sec,
submission_score, body length, config) and the first 600 chars of
the submission body.
