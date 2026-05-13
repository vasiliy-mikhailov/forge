# `src/reward_bench/use_cases/condenser_port.py`

`CondenserPort` is the application-layer abstraction over the
SPEC.md context-compaction step.

## Protocol

    class CondenserPort(Protocol):
        def condense(
            self,
            messages: tuple[dict, ...],
            config: CondenserConfig,
        ) -> tuple[dict, ...]:
            ...

`messages` is the agent-loop's conversation history (OpenAI-style
`{role, content}` dicts). The condenser MAY return a shorter tuple
in which older turns are replaced by a summary turn. The most
recent `config.keep_recent` turns are NEVER summarised — they pass
through unchanged.

## NullCondenser

A trivial in-module implementation that returns
`tuple(messages)` unchanged. Useful as the default in tests + when
the conversation is below the trigger budget.

## Layer purity

`use_cases/` lives at the application layer: imports only
`entities/` and standard library. No HTTP, no Docker, no LLM call.
Concrete LLM-backed adapters live in `adapters/`.
