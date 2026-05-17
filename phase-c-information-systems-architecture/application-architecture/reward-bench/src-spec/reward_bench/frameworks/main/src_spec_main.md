# `src/reward_bench/frameworks/main.py`
`main` is the bench's composition root — wires concrete adapters to
use cases, runs the agent loop against a live vLLM endpoint, emits
an `AttemptResult`.
## Function
 def main(model_id: str = 'qwen3.6-27b-awq',
 seeds: Iterable[int] = range(1000, 1020),
 config: BenchConfig = BenchConfig(),) -> AttemptResult
The `config` parameter is the [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
knob panel — `max_iters`, `temperature`, `n_trials`,
`max_no_improve`, `finish_floor`. Default `BenchConfig()` yields the
 defaults; tests pass smaller values for fast runs.
## Steps
1. Look `model_id` up in `MODEL_REGISTRY`; fail loudly if missing.
2. Call `ensure_serving()` to guarantee the lab vLLM container is up.
3. Create a workspace; run `agent_loop.run_loop(...,
 max_iters=config.max_iters, temperature=config.temperature)`.
4. Try to `load_submission`; access `module.Solver`. On
 `AttributeError` (no `Solver`) or `FileNotFoundError` (no
 submission file), return a sentinel `AttemptResult(n_games=0,
 games=(),...)`. Per
 [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md).
5. Happy path: `score_submission(Solver, seeds,
 GameBoard2048Adapter())` produces a populated `AttemptResult`.
6. Print key fields; return.
## Knob propagation
- `config.max_iters` → `agent_loop.run_loop(max_iters=...)`.
- `config.temperature` → `agent_loop.run_loop(temperature=...)` →
 `_call_model(temperature=...)`.
- `config.n_trials` is NOT used here — that's the multi-trial use
 case's job (future cycle).
- `config.max_no_improve`, `config.finish_floor` — not yet enforced
 inside `agent_loop` (future cycle).
## Entry point
`src/reward_bench/__main__.py` is a two-line shim:
 from src.reward_bench.frameworks.main import main
 main()
`python -m src.reward_bench` runs the bench with the
defaults. Tests pass an explicit `config` to keep wall time bounded.
