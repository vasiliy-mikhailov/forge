# `src_spec_when_orchestrator_called_then_returns_iterable_of_submissions`

[`../../../src/ports/orchestrator.py`](../../../src/ports/orchestrator.py)
defines the `Orchestrator` runtime-boundary contract per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§7 for "enumerate candidate submissions under a config". The bench
takes `argmax (score env)` over this enumeration.

## Contract

```python
class Orchestrator(Protocol):
    def orchestrate(self, env, cfg) -> Iterable[Submission]: ...
```

Semantics:

- `env` is the bench environment (canonical scorer + tasks dir +
  whatever else `score :: Env -> Submission -> Score` reads).
- `cfg` is a `BenchConfig` — wall-time budget, iter cap, model id.
- Returns an iterable of `Submission` value objects (frozen — see
  [`src/tier1/entities/submission.py`](../../../src/tier1/entities/submission.py)).
  Streaming-or-batch is up to the adapter.

## Adapter manifest

None yet — adapters land in subsequent cycles:

- `orchestrate_ralph_single_context` (planned): wraps the existing
  `src.tier1.agent_loop.run_loop` long-context strategy.
- `orchestrate_subagent_per_iter` (planned): spawns a fresh subagent
  per iter, likely via OpenHands. Until then a homegrown prototype
  may serve.

The Port exists ahead of the adapters so the bench-side code can be
written against the abstraction; adapter implementations swap freely
without touching `bench`.
