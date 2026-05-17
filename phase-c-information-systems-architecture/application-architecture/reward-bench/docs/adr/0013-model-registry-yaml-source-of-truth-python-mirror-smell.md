# ADR 0013 — Model registry: YAML is source of truth, Python mirror is a smell

## Status

Accepted (cycle 99a). Reconciliation queued as cycle 101 (small,
mechanical edits).

## Context

Two model registries currently disagree:

1. **YAML (source of truth):** `wiki-compiler/configs/models.yml` per
   [wiki-compiler ADR 0008](../../../wiki-compiler/docs/adr/0008-model-registry-single-source-of-truth.md).
   Consumed by `load-active-model.sh`, `run-battery.sh`,
   `reward-bench/src/reward_bench/frameworks/run_battery.py`.

2. **Python tuple (mirror):**
   `reward-bench/src/reward_bench/use_cases/model_registry.py::MODEL_REGISTRY`
   — `ModelTarget` dataclasses copy-pasted from the YAML. Consumed by
   `_pick_model`, `test_smoke_all_models.py`, `ensure_serving_model`.

The mirror gained extra fields (`served_name`, `tool_call_parser`,
`max_model_len`) that also exist in YAML.

Drift observed:
- YAML's `qwen3.6-27b-awq-int4-community` has `bench_skip: true`;
  Python includes `qwen3.6-27b-awq` (different id).
- YAML's `qwen3.6-35b-a3b-fp8` (`bench_skip: true`) is omitted from Python.
- A new YAML model needs manual transcription.

Every change must be made in two places.

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

- `ModelTarget` shape unchanged — refactor only.
- `bench_skip: true` entries EXCLUDED (matches `select_battery` rule).
- Import-time caching; YAML not edited at runtime.
- Test fixtures may build their own tuple.

## Consequences

+ New model = one-line YAML add; Python mirror updates automatically.
+ Drift between `make reward-battery` and `make reward-bench MODEL=`
  becomes impossible.
+ `run_battery.py::load_models` is now load-bearing; pin its shape.
- PyYAML at import time for everyone importing `MODEL_REGISTRY`
  (already required by `run_battery`).
- YAML parse failure crashes test collection; mitigated by a tight
  `load_models` contract test.

## Path forward

- Rewrite `model_registry.py` per snippet.
- `test_model_registry.py` pinning: non-empty tuple of `ModelTarget`,
  `bench_skip` excluded, unique ids.
- Delete the hand-maintained literal.
- Cross-link from wiki-compiler ADR 0008.

## Related

- [Wiki-compiler ADR 0008](../../../wiki-compiler/docs/adr/0008-model-registry-single-source-of-truth.md)
  — upstream source-of-truth decision.
- [ADR 0009](0009-multi-model-smoke-bench-convention.md) — smoke
  iterates `MODEL_REGISTRY`.
