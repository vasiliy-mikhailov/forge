# `src_spec_fake_solution_generator`

[`../../../../src/adapters/fakes/fake_solution_generator.py`](../../../../src/adapters/fakes/fake_solution_generator.py)
is the test double for the §2 `SolutionGenerator` Port.

Constructor:

```python
FakeSolutionGenerator(body: str)
```

Method:

```python
def generate(self, snapshot: ContextSnapshot) -> str:
    return self._body
```

Returns the constructor-supplied body verbatim regardless of
snapshot. The snapshot is ignored — tests pin orchestrator
behaviour, not generator behaviour.
