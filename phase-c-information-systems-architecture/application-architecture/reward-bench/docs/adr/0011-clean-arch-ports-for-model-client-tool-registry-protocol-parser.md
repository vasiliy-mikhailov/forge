# ADR 0011 — Clean-architecture ports for model client, tool registry, and protocol parser

## Status

Accepted (cycle 97). Implementation will land across cycles 98–100
(small, atomic CATS cycles; see §Path forward).

## Context

After cycle 96 the bench is functionally complete for tier 1 with the
qwen / gemma / llama / mistral / devstral / gpt-oss family of vLLM-served
models. The cost has been steady architectural drift. `src/tier1/agent_loop.py`
now does four jobs in one module:

1. `_call_model` — HTTP client + OpenAI Chat-Completions payload
   shape + bearer auth + (cycle 96) `tools=[...]` schema advertisement.
2. `TOOL_SCHEMAS` — the catalog of tools the bench exposes
   (currently `view`, `execute_submission`, `finish`).
3. `execute_tool` — name-keyed dispatch (`if name == 'view'... elif
   name == 'execute_submission'... elif name == 'finish'...`) with each
   handler inlined.
4. `parse_tool_calls` — protocol-A parser (text-fenced) fused with
   protocol-B parser (OpenAI structured) into one function, with
   cycle-96 SentencePiece-leak stripping bolted on.

`src/tier1/inference.py::ensure_serving_model` similarly knows about
specific vLLM CLI flags (`--tool-call-parser`, `--enable-auto-tool-choice`)
and about Docker container management.

`ModelTarget` carries vLLM-specific fields (`tool_call_parser`,
`served_name`) that leak into the entity layer.

This is acceptable today because:
  - There is exactly one serving stack (vLLM in a Docker container).
  - There is exactly one tier wired (tier 1).
  - There is exactly one prompt-protocol family (the cycle-9/58 fenced-text
    contract, with cycle-83/96 OpenAI-structured fallback as a vLLM-side
    adaptation of the same surface).

It stops being acceptable as soon as:
  - SPEC.md tiers 2–4 land. Each tier has a different submission shape
    and therefore a different tool surface (langgraph build steps,
    OpenHands orchestrator function, etc.). Adding a tool means editing
    `execute_tool` directly.
  - We A/B against the Claude or OpenAI API directly (not via vLLM).
    Today this is a `_call_model` rewrite.
  - A model emits in a third protocol surface (e.g., Anthropic tool-use
    blocks). Today this is a `parse_tool_calls` rewrite.
  - We want to fixture-test `run_loop` against a deterministic in-memory
    `ModelClient` without monkeypatching internals.

## Decision

Introduce three ports under `src/ports/`, with adapters under
`src/adapters/`, leaving the entity and use-case layers untouched.

### Ports

```python
# src/ports/model_client.py
class AssistantReply(TypedDict):
    content: str
    tool_calls: list[dict]   # OpenAI tool_calls shape, possibly empty

class ModelClient(Protocol):
    def call(
        self,
        messages: list[dict],
        *,
        tools: list[dict],
        temperature: float = 0.0,
        max_tokens: int = 12288,
        model_id: str | None = None,
    ) -> AssistantReply: ...
```

```python
# src/ports/tool_registry.py
class ToolCall(NamedTuple):
    name: str
    args: dict

class ToolContext(TypedDict):
    workspace: Path
    env_dir: Path
    tasks_dir: Path
    dev_hard_wall_sec: float | None

class ToolRegistry(Protocol):
    schemas: tuple[dict, ...]
    def dispatch(self, name: str, args: dict, ctx: ToolContext) -> str: ...
```

```python
# src/ports/protocol_parser.py
class ProtocolParser(Protocol):
    def extract(self, reply: AssistantReply) -> list[ToolCall]: ...
```

### Adapters

- `src/adapters/vllm_openai_client.py::VllmOpenAIClient(ModelClient)`
  Wraps current `_call_model` HTTP path; takes `base_url`, `api_key`,
  default `model_id` at construction time.
- `src/adapters/parsers/fenced_text_parser.py::FencedTextParser(ProtocolParser)`
  Cycle-9/58 fenced-block parser. Reads `reply.content`.
- `src/adapters/parsers/structured_openai_parser.py::StructuredOpenAIParser(ProtocolParser)`
  Cycle-83 fallback parser. Reads `reply.tool_calls`. Cycle-96
  SentencePiece-leak stripping lives here.
- `src/adapters/parsers/composite_parser.py::CompositeParser(ProtocolParser)`
  Tries each child parser in order; first non-empty result wins.
  Production default: `CompositeParser([FencedTextParser(),
  StructuredOpenAIParser()])`.
- `src/adapters/tier1_tool_registry.py::Tier1ToolRegistry(ToolRegistry)`
  Owns the three tier-1 tools (`view`, `execute_submission`, `finish`)
  plus their schemas. Tier-2+ get their own registry classes.

### Use-case wiring

`run_loop(workspace, env_dir, tasks_dir, model_client, tool_registry,
protocol_parser, max_iters, ...)` becomes the public seam.
`main()` constructs production defaults; tests inject fakes.

`run_loop` no longer:
  - imports `urllib.request` or knows about vLLM
  - hard-codes which tools exist
  - knows about two parser surfaces

It just orchestrates: `reply = client.call(...); calls =
parser.extract(reply); for name, args in calls: obs =
registry.dispatch(name, args, ctx)`.

## Migration constraint: zero-behaviour-change

Each refactor cycle MUST be a no-op for the bench output. This is
testable in two ways:
  1. The cycle-71 verification bench (Qwen3.6-27B-AWQ → 15.9k mean)
     stays green at every cycle.
  2. Existing tests in `tests/tier1/test_agent_loop.py` continue to
     pass without contract changes; new ports tests cover the new
     seams.

## Consequences

+ Tier-2+ tool surfaces become a `ToolRegistry` swap in `main()`.
+ Anthropic / OpenAI direct mode becomes a new `ModelClient` adapter.
+ The bench-side bugs from ADR 0010 (mistral special tokens) and
  cycle 96 (SentencePiece leak) are localized to one adapter file.
+ `run_loop` becomes deterministically fixture-testable without
  monkeypatching `_call_model` / `execute_tool`.
+ Slight indirection cost in tier-1 path (one extra method call per
  ralph iter). Negligible against vLLM latency.
- One transitional cycle where both old and new seams coexist (cycle
  98 introduces the ports as parallel APIs; cycle 99 cuts callers
  over; cycle 100 deletes the old top-level functions).

## Path forward (cycles 98–100)

**Cycle 98**: Introduce ports + adapters; existing top-level functions
delegate to them. No caller changes. Tests for each new adapter.

**Cycle 99**: `run_loop` takes the three ports as parameters
(defaulting to production-shaped factory functions so existing
callers don't break). `main()` constructs the production triple.

**Cycle 100**: Delete the old top-level functions / module-level
constants (`_call_model`, `execute_tool`, `TOOL_SCHEMAS`,
`parse_tool_calls`) once nothing imports them. ADR 0011 marked
"Landed".

Each cycle is small enough to commit independently. Bench parity
re-verified at the end of each cycle (cycle-71 reference run).

## Related

- [ADR 0008](0008-docker-sandboxed-execute-submission-tool.md)
  introduced `execute_submission` — the tool surface that now needs
  to become pluggable.
- [ADR 0010](0010-mistral-special-tokens-incompatible-with-fenced-tool-protocol.md)
  uncovered the parser polyglot need; cycle-96 amendment closed the
  bench-side bug. ADR 0011 prevents the next polyglot need from being
  a `parse_tool_calls` edit.
- Cycle 85 audit flagged the coupling but deferred the refactor
  pending an actual second-protocol use case; ADR 0010 + cycle 96
  was that case.
