# `src/tier1/agent_loop.py` — `run_loop(...)` `condense` parameter

Adds a new optional parameter to the agent loop's main entry:

    def run_loop(
        workspace, env_dir, tasks_dir,
        vllm_base_url, vllm_api_key, max_iters,
        condense: Callable[[Tuple[dict, ...]], Tuple[dict, ...]] = ...,
    ):

## Semantics

- Default value is the identity function: `lambda msgs: tuple(msgs)`.
- Before every `_call_model` invocation, the loop calls
  `messages = list(condense(tuple(messages)))`.
- The condense function MAY shorten the message tuple (by replacing
  older turns with a summary turn); it MUST preserve at least the
  system message and recent turns per
  [`CondenserConfig.keep_recent`](../../reward_bench/entities/condenser_config/src_spec_condenser_config.md)
  (enforced by the concrete adapter, not by `run_loop`).
- The condense function is opaque to the loop — `run_loop` does not
  inspect what was condensed or check sizes. The adapter that wraps
  a `CondenserPort` is responsible for honouring the config.

## Why the parameter is a `Callable`, not a `CondenserPort`

`tier1` is an inner module; per the multi-module dependency rule it
must not import from `reward_bench` (outer). `CondenserPort` lives
in `src/reward_bench/use_cases/`. Typing the parameter as a generic
`Callable` keeps tier1 self-contained; the orchestrator
(`reward_bench.frameworks.main`) adapts a `CondenserPort` instance
to the callable at the boundary:

    condenser = NullCondenser()  # or LlmCondenser(...)
    run_loop(..., condense=lambda msgs: condenser.condense(msgs, config))

## Default behaviour

When called without `condense`, the loop behaves identically to its
pre-cycle-15 form. All existing tests stay green; the cycle 12
end-to-end run produces the same `AttemptResult` as before.
