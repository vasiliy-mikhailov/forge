# ADR 0011 — Clean-architecture ports for model client, tool registry, and protocol parser

## Status

Accepted (cycle 97). Implementation will land across cycles 98–100
(small, atomic CATS cycles; see §Path forward).

## Context

`src/tier1/agent_loop.py` does four jobs:

1. `_call_model` — HTTP client, OpenAI Chat-Completions payload, bearer
   auth, `tools=[...]` advertisement.
2. `TOOL_SCHEMAS` — catalog (`view`, `execute_submission`, `finish`).
3. `execute_tool` — name-keyed dispatch with handlers inlined.
4. `parse_tool_calls` — text-fenced fused with OpenAI-structured,
   plus SentencePiece-leak stripping bolted on.

`src/tier1/inference.py::ensure_serving_model` knows vLLM CLI flags and
Docker container management. `ModelTarget` carries vLLM-specific fields
(`tool_call_parser`, `served_name`) that leak into entities.

Tolerable today: one serving stack (vLLM-in-Docker), one tier, one
protocol family. Stops being tolerable when:

- Tiers 2–4 land — each adds a tool surface; today means editing
  `execute_tool`.
- We A/B against Claude / OpenAI directly — today is a `_call_model`
  rewrite.
- A model emits a third protocol — today is a `parse_tool_calls` rewrite.
- We want to fixture-test `run_loop` without monkeypatching.

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

- `VllmOpenAIClient(ModelClient)` — wraps `_call_model`. Takes
  `base_url`, `api_key`, default `model_id`.
- `FencedTextParser(ProtocolParser)` — reads `reply.content`.
- `StructuredOpenAIParser(ProtocolParser)` — reads `reply.tool_calls`.
  SentencePiece-leak stripping lives here.
- `CompositeParser(ProtocolParser)` — tries children in order; first
  non-empty wins. Production default:
  `CompositeParser([FencedTextParser(), StructuredOpenAIParser()])`.
- `Tier1ToolRegistry(ToolRegistry)` — owns `view`, `execute_submission`,
  `finish` and their schemas. Tier-2+ get their own registries.

### Use-case wiring

`run_loop(workspace, env_dir, tasks_dir, model_client, tool_registry,
protocol_parser, max_iters, ...)`. `main()` constructs production;
tests inject fakes.

`run_loop` no longer imports `urllib.request`, hardcodes tools, or
knows about two parser surfaces. It orchestrates:
`reply = client.call(...); calls = parser.extract(reply); for name,
args in calls: obs = registry.dispatch(name, args, ctx)`.

## Migration constraint: zero-behaviour-change

Each cycle a no-op for bench output: verification bench (15.9 k on
Qwen3.6-27B-AWQ) stays green; existing tests pass; new tests cover
new seams.

## Consequences

+ Tier-2+ tool surfaces become a `ToolRegistry` swap in `main()`.
+ Anthropic / OpenAI direct = new `ModelClient` adapter.
+ Mistral special-tokens and SentencePiece leak localised to one file.
+ `run_loop` fixture-testable without monkeypatching.
+ One extra method call per ralph iter — negligible.
- One transitional cycle where old and new seams coexist.

## Path forward

1. Introduce ports + adapters; old functions delegate. Tests for adapters.
2. `run_loop` takes ports as parameters with production defaults.
   `main()` constructs the triple.
3. Delete old top-level functions (`_call_model`, `execute_tool`,
   `TOOL_SCHEMAS`, `parse_tool_calls`).

## Related

- [ADR 0008](0008-docker-sandboxed-execute-submission-tool.md) —
  introduced `execute_submission`; tool surface now pluggable.
- [ADR 0010](0010-mistral-special-tokens-incompatible-with-fenced-tool-protocol.md)
  — uncovered parser polyglot need.
