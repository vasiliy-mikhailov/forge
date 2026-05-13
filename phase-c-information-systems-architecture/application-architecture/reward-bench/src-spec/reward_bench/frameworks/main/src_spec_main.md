# `src/reward_bench/frameworks/main.py`

`main` is the bench's composition root — the outermost layer that
wires concrete adapters to use cases, runs the agent loop against a
live vLLM endpoint, and emits an `AttemptResult`.

## Function

    def main(
        model_id: str = 'qwen3.6-27b-awq',
        seeds: Iterable[int] = range(1000, 1020),
        max_iters: int = 30,
    ) -> AttemptResult

## Steps

1. Look `model_id` up in `MODEL_REGISTRY`; fail loudly if missing.
2. Call `ensure_serving()` to guarantee the lab vLLM container is up
   and return its base URL.
3. Create a workspace directory and run `agent_loop.run_loop()`
   against the model — produces `submission.py` in the workspace.
4. Try to `harness.load_submission()` the file and access
   `module.Solver`. On `AttributeError` (no `Solver` class) or
   `FileNotFoundError` (no submission written), return a sentinel
   `AttemptResult(n_games=0, games=(), mean_score=0.0, ...)` so
   the bench never crashes on malformed model output.
5. Happy path: instantiate `GameBoard2048Adapter`; call
   `score_submission(solver_factory=Solver, seeds=seeds, env=adapter)`.
6. Print key fields of the `AttemptResult` to stdout for the human
   "watch the bench run" experience.
7. Return the `AttemptResult`.

## Layering

This file is the only place that imports across all four reward-
bench layers AND across modules into tier1's transitional root
files (`tier1/inference.py`, `tier1/agent_loop.py`, `tier1/harness.py`).
Cross-module reach is acceptable in the composition root.

## Entry point

`src/reward_bench/__main__.py` is a two-line shim:

    from src.reward_bench.frameworks.main import main
    main()

so `python -m src.reward_bench` runs the bench from the repo root.
