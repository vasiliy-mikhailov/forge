# `src_spec_openhands_solution_generator`

[`../../../../src/reward_bench/adapters/openhands_solution_generator.py`](../../../../src/reward_bench/adapters/openhands_solution_generator.py)
is the OpenHands-backed `SolutionGenerator` per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§4 (the committed implementation of the SolutionGenerator runtime).

Constructor:

```python
OpenHandsSolutionGenerator(*, _openhands_runner: Callable[[str], str] | None = None)
```

`_openhands_runner` is injectable so the adapter is unit-testable
without the OpenHands SDK installed. Default binding constructs
an OpenHands `Conversation`, runs it on the prompt, returns the
final submission body.

Method:

```python
def generate(self, snapshot: ContextSnapshot) -> str:
    prompt = self._render_prompt(snapshot)
    return self._runner(prompt)
```

The prompt rendering includes `snapshot.env_spec`,
`snapshot.best_so_far` (body + score), `snapshot.history_digest`
(prior bodies + scores), and the remaining-budget fields. Each
field appears in a stable place so the OpenHands agent can find
it deterministically.
