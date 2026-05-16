# ADR 0009 — Multi-model smoke bench convention

## Context

`MODEL_REGISTRY` has 22 candidate models. A "smoke" sweep is a
fast-feedback gate that proves each model can drive the bench loop to
produce at least one working `execute_submission` body — not a full
canonical campaign.

The cheap signal is `best_dev_mean > 0`: the model emitted at least
one submission whose dev-seed games scored above zero. This is
significantly less expensive than the canonical 20-seed eval that
ADR 0003 specifies for full campaigns.

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

- **`max_iters=100`** — gives slow-starter models (e.g.
  qwen3.6-27b-awq, which emits its first `execute_submission` around
  iter 11-14) a fair shot.
- **`smoke_early_stop=True`** — bench forces `finished=True` on the
  first iter where `best_dev_mean > 0`. Strong models would otherwise
  grind all 100 iters.
- **Canonical scoring is skipped in smoke mode.** The smoke signal
  (`best_dev_mean > 0`) is the verdict; running canonical adds
  ~10 min per trial for no additional information.

## Smoke success criterion

`best_dev_mean > 0`. A `0.0` or `None` result is a **bench-side bug
signal**, not a model verdict. The model produced something but the
dev games scored zero across all 5 seeds — investigate the bench
path (parser, sandbox, env), not the model's intelligence.

## Consequences

+ Per-model wall time: ~30 s warm-up + N×iter (~1-2s/iter) until
  first positive dev_mean. Median: ~3 min/model on warm vLLM.
+ Each smoke artifact captures the model's first working submission
  body, useful for trajectory analysis.
+ A 22-model sweep finishes in ~1 hour wall once vLLM is warm.
- The 100-iter ceiling biases toward fast-starters; very slow models
  may need a separate config. Inspect the no_tool_streak signal in
  the artifact to distinguish "slow starter" from "incompatible
  protocol".

## Related

- [ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) —
  full canonical campaign defaults.
- [ADR 0015](0015-canonical-bench-hard-wall-sec-300.md) — canonical
  hard_wall_sec (separate from smoke's).
- Test pin:
  [`test_smoke_all_models.py`](../../tests/reward_bench/frameworks/smoke/test_smoke_all_models.py).
