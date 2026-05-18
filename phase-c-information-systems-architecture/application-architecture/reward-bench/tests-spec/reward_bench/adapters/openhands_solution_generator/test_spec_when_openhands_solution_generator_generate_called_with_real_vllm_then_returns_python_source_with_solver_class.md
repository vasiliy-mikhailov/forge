# `test_when_openhands_solution_generator_generate_called_with_real_vllm_then_returns_python_source_with_solver_class`

End-to-end live test of the §4 `OpenHandsSolutionGenerator` against
real OpenHands SDK + real vLLM. Validates that the
`generate(snapshot)` call:

1. Renders the snapshot into a prompt
2. Constructs an OpenHands `LLM` / `Agent` / `Conversation` from
   `model_client.base_url` / `.api_key` / `.model_id`
3. Sends the prompt
4. Runs the agent to completion
5. Reads `submission.py` from the workspace
6. Returns the body as a string

If this passes, the §2 three-role separation + §4 OpenHands
binding is live.

- **Arrange**: `VllmOpenAIClient(vllm_base_url, vllm_api_key,
  'qwen3.6-27b-awq')`; `OpenHandsSolutionGenerator(model_client=mc)`;
  a `ContextSnapshot` whose `env_spec` instructs the agent to
  write `class Solver: ...` to `/workspace/submission.py`.
- **Act**: `body = generator.generate(snapshot)`.
- **Assert**: `'class Solver' in body`.

Test code: [`../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py`](../../../../tests/reward_bench/adapters/test_openhands_solution_generator.py)::`test_when_openhands_solution_generator_generate_called_with_real_vllm_then_returns_python_source_with_solver_class`.

## Model client injection point

- **Seam**: real `VllmOpenAIClient`; default OpenHands runner
  factory.
- **Mode**: **live** — real SDK, real LLM, real Conversation.

## Runtime scope

> **Runtime scope**: live — OpenHands Conversation against real vLLM. ~30-90s realistic.
