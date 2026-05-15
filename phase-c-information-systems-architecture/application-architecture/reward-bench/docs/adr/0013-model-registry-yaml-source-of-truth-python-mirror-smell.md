# ADR 0013 — Model registry: YAML is source of truth, Python mirror is a smell

## Status

Accepted (cycle 99a). Reconciliation queued as cycle 101 (small,
mechanical edits).

## Context

There are currently two model registries that disagree about the
same conceptual data:

1. **YAML (source of truth):**
   `wiki-compiler/configs/models.yml` — the
   [wiki-compiler ADR 0008](../../../wiki-compiler/docs/adr/0008-model-registry-single-source-of-truth.md)
   declares this file the single source of truth for vLLM serving
   configuration. It's consumed by:
   - `wiki-compiler/bin/load-active-model.sh` (renders the runtime
     env from `INFERENCE_ACTIVE_MODEL_ID`).
   - `wiki-compiler/bin/run-battery.sh` (legacy battery iterator).
   - `reward-bench/src/reward_bench/frameworks/run_battery.py`
     (cycle 94 `make reward-battery` implementation).

2. **Python tuple (mirror):**
   `reward-bench/src/reward_bench/use_cases/model_registry.py::MODEL_REGISTRY`
   — a tuple of `ModelTarget` dataclasses copy-pasted from the YAML.
   Consumed by:
   - `_pick_model(model_id)` in `frameworks/main.py`.
   - `test_smoke_all_models.py` parametrize source.
   - `ensure_serving_model(target)` (the vLLM container provisioner).

The Python mirror was introduced in cycle 11 when `wiki-compiler` was
the only known consumer and `reward-bench` shared the Blackwell GPU.
A type-safe `ModelTarget` was useful for `main()`. Over cycles 73 + 74
the mirror gained extra fields (`served_name`, `tool_call_parser`,
`max_model_len`) that exist in the YAML too.

The drift is real:
- The YAML lists `qwen3.6-27b-awq-int4-community` with `bench_skip:
  true`. The Python `MODEL_REGISTRY` includes `qwen3.6-27b-awq`
  (different id) and skips the community variant entirely.
- The YAML's `qwen3.6-35b-a3b-fp8` has `bench_skip: true`. The Python
  mirror omits it.
- A new model in the YAML doesn't appear in `MODEL_REGISTRY` until
  someone manually transcribes it.

This forces every model-registry change to be made in two places.

## Decision

**The YAML is the source of truth.** The Python `MODEL_REGISTRY`
becomes a thin wrapper that reads + caches the YAML at import time:

```python
# src/reward_bench/use_cases/model_registry.py
from src.reward_bench.frameworks.run_battery import load_models

def _build_registry() -> tuple[ModelTarget, ...]:
    models = load_models(_REGISTRY_PATH)
    return tuple(
        ModelTarget(
            id=m["id"],
            hf_path=m["hf"],
            served_name=m["served_name"],
            max_model_len=m["max_model_len"],
            tool_call_parser=m["tool_call_parser"],
        )
        for m in models
        if not m.get("bench_skip", False)
    )

MODEL_REGISTRY: tuple[ModelTarget, ...] = _build_registry()
```

Single edit (the YAML) propagates to both `make reward-battery` and
the Python `main()` / smoke parametrization automatically.

## Constraints

- The Python `ModelTarget` dataclass shape stays exactly as today —
  this is a refactor, not a contract change. Existing callers don't
  see any difference.
- `bench_skip: true` entries are EXCLUDED from `MODEL_REGISTRY`
  (matches the cycle-94 `select_battery` rule and current Python
  manual exclusion list).
- Import-time caching is fine; the YAML is not edited at runtime.
- Test fixtures that want a custom registry build their own tuple;
  the wrapper doesn't preclude that.

## Consequences

+ A new model is a one-line YAML add. The Python mirror updates
  automatically.
+ Drift between `make reward-battery` and `make reward-bench MODEL=`
  becomes impossible — both read the same source.
+ Cycle-94 `run_battery.py::load_models` is now a load-bearing
  function; pin its return shape with a test_spec.
- One new import-time dependency on PyYAML for everyone importing
  `MODEL_REGISTRY` (already required by `run_battery`).
- A YAML parse failure crashes test collection; mitigated by
  pinning the registry path + a tight `load_models` contract test.

## Path forward

**Cycle 101** (small, mechanical):
- Rewrite `src/reward_bench/use_cases/model_registry.py` per the
  snippet above.
- Add `tests/reward_bench/use_cases/test_model_registry.py` pinning:
  - `MODEL_REGISTRY` is a non-empty tuple of `ModelTarget`s.
  - `bench_skip: true` entries from the YAML are EXCLUDED.
  - Every entry's `id` is unique.
- Delete the hand-maintained `MODEL_REGISTRY` literal.
- Update `wiki-compiler/docs/adr/0008` cross-link to mention
  this ADR as the consuming side.

## Related

- [Wiki-compiler ADR 0008](../../../wiki-compiler/docs/adr/0008-model-registry-single-source-of-truth.md)
  — the upstream "YAML is single source of truth" decision.
- [ADR 0009](0009-multi-model-smoke-bench-convention.md)
  — smoke v2 convention; depends on `MODEL_REGISTRY` to iterate.
- Cycle 94 (`make reward-battery`) — already reads the YAML
  directly; this ADR aligns the smoke / `main()` paths with it.
