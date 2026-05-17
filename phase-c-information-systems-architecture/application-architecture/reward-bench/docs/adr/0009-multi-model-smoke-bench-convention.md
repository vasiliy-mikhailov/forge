# ADR 0009 — Multi-model smoke bench convention

## Context

`MODEL_REGISTRY` has 22 models. A "smoke" sweep is a fast-feedback gate
proving each model can drive the loop to one working
`execute_submission` — not a full canonical campaign.

Cheap signal: `best_dev_mean > 0`. Far cheaper than canonical 20-seed.

## Decision

Smoke bench config:

```
SMOKE_CONFIG = BenchConfig(
    max_iters=100,
    n_trials=1,
    temperature=0.7,
    finish_floor=0.0,
    hard_wall_sec=60.0,
    supervisor_every_k=0,
    smoke_early_stop=True,
)
```

- **`max_iters=100`** — gives slow starters (qwen3.6-27b-awq emits
  first `execute_submission` around iter 11-14) a fair shot.
- **`smoke_early_stop=True`** — forces `finished=True` on first iter
  with `best_dev_mean > 0`; otherwise strong models grind all 100.
- **Canonical scoring skipped in smoke.** The smoke signal is the
  verdict; canonical adds ~10 min per trial for no extra info.

## Smoke success criterion

`best_dev_mean > 0`. A `0.0` / `None` is a **bench-side bug signal**,
not a model verdict — investigate parser/sandbox/env.

## Consequences

+ Per-model wall time: ~30 s warm-up + ~1-2 s/iter to first positive
  dev_mean. Median ~3 min/model on warm vLLM.
+ Each artifact captures first working submission body.
+ 22-model sweep ~1 hour once vLLM warm.
- 100-iter ceiling biases toward fast-starters; inspect
  `no_tool_streak` to distinguish slow-start from incompatible protocol.

## Related

- [ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) —
  full canonical campaign defaults.
- [ADR 0015](0015-canonical-bench-hard-wall-sec-300.md) — canonical
  hard_wall_sec (separate from smoke's).
- Test pin:
  [`test_smoke_all_models.py`](../../tests/reward_bench/frameworks/smoke/test_smoke_all_models.py).
