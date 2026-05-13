# `src/reward_bench/entities/bench_config.py`

`BenchConfig` is a frozen dataclass — the orchestrator-side knob
panel for a bench run. Defaults are codified in
[ADR 0003](../../../../docs/adr/0003-bench-defaults-500-iters-10-trials-temp-0.7.md);
this entity is the Python embodiment of those defaults.

## Fields

| Field            | Type    | Default   | Meaning                                                          |
| ---------------- | ------- | --------- | ---------------------------------------------------------------- |
| `max_iters`      | `int`   | `500`     | Turn budget per agent-loop attempt.                              |
| `n_trials`       | `int`   | `10`      | Independent attempts per model; reported mean aggregates them.   |
| `temperature`    | `float` | `0.7`     | Stage-1 author-loop sampling temperature.                        |
| `max_no_improve` | `int`   | `999999`  | Reject `finish` if dev_runner score did not improve in N turns.  |
| `finish_floor`   | `float` | `0.0`     | Reject `finish` if dev_runner score is below this floor.         |
| `hard_wall_sec`  | `float` | `0.0`     | Aggregate walltime cap (cycle 23 score_submission knob). 0 = disabled (per ADR 0003 + 0006).         |

Notes on what is NOT in `BenchConfig`:

- `max_model_len` lives on `ModelTarget` (per-model vLLM config).
- Condenser `model_id` is decided at the wiring layer; per
  [ADR 0001](../../../../docs/adr/0001-condenser-uses-same-model-as-bench.md)
  it equals the bench model's `id`.
- `hard_wall_sec` is now a BenchConfig field (cycle 24) AND an AttemptResult observation field. Input lives on config; output reflects what cap applied to a given run.
  Default 0 (disabled), per SPEC.md.

## Properties

Frozen, no methods. Pure data.
