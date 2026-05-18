# `src_spec_fake_orchestrator`

[`../../../../src/adapters/fakes/fake_orchestrator.py`](../../../../src/adapters/fakes/fake_orchestrator.py)
is the test double for the §7 `Orchestrator` Port per ADR-0018.
Scripted in-memory `Orchestrator`.

Constructor:

```python
FakeOrchestrator(submissions: tuple[Submission, ...] | list[Submission])
```

Method:

```python
def orchestrate(self, env, cfg) -> Iterable[Submission]: ...
```

Yields the constructor-supplied submissions verbatim. No filtering,
no derivation — the script IS the result.
