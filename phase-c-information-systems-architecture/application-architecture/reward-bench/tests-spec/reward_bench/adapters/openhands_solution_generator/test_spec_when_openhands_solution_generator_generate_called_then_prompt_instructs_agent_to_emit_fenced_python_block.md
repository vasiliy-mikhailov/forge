# `test_when_openhands_solution_generator_generate_called_then_prompt_instructs_agent_to_emit_fenced_python_block`

Pins §4 binding interface in
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md):
the prompt rendered by `OpenHandsSolutionGenerator._render_prompt`
includes an Output section telling the agent to emit its final
Solver code as a fenced ```` ```python ... ``` ```` block in its
last assistant message. The runner factory extracts that block as
the body.

The boundary contract is the fenced block — any file paths the
agent uses internally for its dev-testing scratch are out of
scope of this test. §4's "no file IO across the binding" means
the runner does not read a file the agent wrote; it does NOT
mean the agent can't write to its own scratch.

- **Arrange**: a stub runner; a minimal `ContextSnapshot` with
  `env_spec='SPEC'`.
- **Act**: `adapter.generate(snap)`.
- **Assert**: captured prompt contains `\`\`\`python`; mentions
  `fenced` or `last assistant message`; contains `# Output`
  section header.

Test code: [`../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py`](../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py)::`test_when_openhands_solution_generator_generate_called_then_prompt_instructs_agent_to_emit_fenced_python_block`.

## Model client injection point

- **Seam**: stub `_openhands_runner` callable.
- **Mode**: **fake** — no SDK, no model.

## Runtime scope

> **Runtime scope**: unit only — pure prompt-shape assertion.
