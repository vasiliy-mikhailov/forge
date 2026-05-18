# `src_spec_solution_generator`

[`../../../src/ports/solution_generator.py`](../../../src/ports/solution_generator.py)
defines the `SolutionGenerator` Port per
[`../../../SOLUTION-ARCHITECTURE.md`](../../../SOLUTION-ARCHITECTURE.md)
§2.

## Contract

```python
class SolutionGenerator(Protocol):
    def generate(self, snapshot: ContextSnapshot) -> str: ...
```

- `snapshot` is a fresh `ContextSnapshot` constructed by the
  orchestrator from cumulative state.
- Returns the SolverBody as a Python source string.
- Pure with respect to in-memory state — no memory across calls
  except what the snapshot carries. Side effects (LLM inference)
  sit at the edge inside the adapter.

## Adapter manifest

- `FakeSolutionGenerator` (planned) — scripted body return for
  unit tests.
- `OpenHandsSolutionGenerator` (planned) — production adapter
  that constructs an OpenHands task per call.
