# `src/reward_bench/entities/bench_config.py`
`BenchConfig` is a frozen dataclass — the orchestrator-side knob
panel for a bench run. Defaults are codified in
[SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md);
this entity is the Python embodiment of those defaults.
## Fields
| Field | Type | Default | Meaning |
| ---------------- | ------- | --------- | ---------------------------------------------------------------- |
| `max_iters` | `int` | `500` | Turn budget per agent-loop attempt. |
| `n_trials` | `int` | `10` | Independent attempts per model; reported mean aggregates them. |
| `temperature` | `float` | `0.7` | Stage-1 author-loop sampling temperature. |
| `max_no_improve` | `int` | `999999` | Reject `finish` if dev_runner score did not improve in N turns. |
| `finish_floor` | `float` | `0.0` | Reject `finish` if dev_runner score is below this floor. |
| `hard_wall_sec` | `float` | `0.0` | Aggregate walltime cap. 0 = disabled. |
Notes on what is NOT in `BenchConfig`:
- `max_model_len` lives on `ModelTarget` (per-model vLLM config).
- Condenser `model_id` is decided at the wiring layer; per
 [SOLUTION-ARCHITECTURE](../../../../SOLUTION-ARCHITECTURE.md)
 it equals the bench model's `id`.
- `hard_wall_sec` is now a BenchConfig field AND an AttemptResult observation field. Input lives on config; output reflects what cap applied to a given run.
 Default 0 (disabled), per SPEC.md.
## Properties
Frozen, no methods. Pure data.
