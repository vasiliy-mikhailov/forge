# `test_when_openhands_solution_generator_generate_called_then_prompt_instructs_agent_to_emit_fenced_python_block`

Pins §4 binding interface in
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md):
the prompt rendered by `OpenHandsSolutionGenerator._render_prompt`
includes an Output section telling the agent to emit its final
Solver code as a fenced ```` ```python ... ``` ```` block in its
last assistant message. The runner factory extracts that block as
the body.

The test also guards the negative case: the prompt must NOT
instruct the agent to write `submission.py` or use `/workspace/`
paths — §4 says no file IO across the binding.

- **Arrange**: a stub runner; a minimal `ContextSnapshot` with
  `env_spec='SPEC'`.
- **Act**: `adapter.generate(snap)`.
- **Assert**: captured prompt contains `\`\`\`python`; mentions
  `fenced` or `last assistant message`; does NOT contain
  `submission.py` or `/workspace/`.

Test code: [`../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py`](../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py)::`test_when_openhands_solution_generator_generate_called_then_prompt_instructs_agent_to_emit_fenced_python_block`.

## Model client injection point

- **Seam**: stub `_openhands_runner` callable.
- **Mode**: **fake** — no SDK, no model.

## Runtime scope

> **Runtime scope**: unit only — pure prompt-shape assertion.
