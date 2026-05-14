# `src_spec_llm_supervisor`

`src.reward_bench.adapters.llm_supervisor.LlmSupervisor` implements
[`SupervisorPort`](../../../use_cases/supervisor_port/src_spec_supervisor_port.md)
by delegating plateau judgment to the bench LLM under test, per [ADR
0001](../../../../docs/adr/0001-condenser-uses-same-model-as-bench.md)
(same model as bench) + [ADR 0005](
../../../../docs/adr/0005-plateau-detection-supervisor-via-llm-self-judgment.md)
(LLM self-judges plateau from sweep data).

Construction: `LlmSupervisor(ask, model_id)` where `ask` is a
`Callable[[str], str]` that takes a rendered prompt and returns the
model's reply text. The wiring layer (`frameworks/main`) supplies an
`ask` backed by the bench-model vLLM endpoint.

`judge(sweep)` flow:

1. **Render**: build a JSON-format prompt from the sweep tuples per
   ADR 0005's prescribed schema. The prompt asks the model to reply
   with `{"plateau": bool, "reasoning": str, "stop_recommended": bool}`
   and instructs CONSERVATIVE bias (only stop if confident further
   iterations would not improve).
2. **Ask**: `reply = ask(prompt)`.
3. **Parse**: locate the first JSON object in the reply (tolerant to
   markdown fences, leading prose, trailing commentary). Extract the
   three fields with type coercion to bool/str.
4. **Wrap**: return `SupervisorDecision(plateau, stop_recommended,
   reasoning)`.

**Error handling** (per CATS no-silent-fix discipline, but applied to
the LLM-reply-fragility surface): if rendering, asking, or parsing
fails for any reason — JSON malformed, network error, missing keys,
wrong types — `judge` MUST return a CONSERVATIVE fallback
`SupervisorDecision(plateau=False, stop_recommended=False,
reasoning='supervisor parse-error: <details>')`. The agent loop never
sees an exception from the supervisor; a flaky supervisor degrades
to "keep going", never to "stop accidentally".

Allowed imports: `json`, `re`, `typing.Callable`, `typing.Tuple`,
`src.reward_bench.entities.supervisor_decision`,
`src.reward_bench.use_cases.supervisor_port` (for the `Sample` alias).
