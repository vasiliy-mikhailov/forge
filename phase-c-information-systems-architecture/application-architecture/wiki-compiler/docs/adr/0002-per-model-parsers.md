# ADR 0002 — tool-call and reasoning parsers are a per-model-family concern

## Status
Accepted (2026-04-25).

## Context
vLLM serves an OpenAI-compatible API but the underlying open-weight
models emit tool calls and chain-of-thought in **family-specific
formats**. The OpenAI client expects:

- `message.tool_calls[]` — a structured array of `{name, arguments}` objects.
- `message.content` — clean assistant text, no chain-of-thought, no tool-call markup.
- `message.reasoning` (or `reasoning_content`) — the chain-of-thought, separated.

vLLM bridges the gap with two configurable extractors:

- `--tool-call-parser <name>` — converts the model's tool-call format
  to OpenAI `tool_calls[]`.
- `--reasoning-parser <name>` — extracts `<think>...</think>` (or
  equivalent) blocks into `reasoning` / `reasoning_content`.

Without a matching parser the model's raw output ends up in
`message.content`, where it confuses agent harnesses (tool calls
silently dropped, reasoning leaked, dangling closing tags).

## Concrete failure that drove this ADR
First deploy used `--tool-call-parser hermes` for `Qwen3-32B-AWQ`,
based on the (mis)assumption that "hermes-style" tool calls are
universal. The simple curl test ("47*53 → calculator") looked fine —
parser produced a clean `tool_calls[]` block.

Then Hermes Agent (the laptop client) connected, exchanged a few
turns, and **silently wedged**. The vLLM logs showed `200 OK`
responses; the laptop showed an agent stalled with the fragment
`view function will help` as `message.content` — Qwen3 had emitted a
natural-language *description* of the tool it wanted to call, not an
extractable tool-call block. The hermes parser couldn't find what it
wasn't looking for, so the chat content (the description) passed
through and Hermes Agent treated it as an answer, not an action.

Switching to `--tool-call-parser qwen3_xml` plus
`--reasoning-parser qwen3` produced clean per-field separation
(`content: null`, populated `reasoning`, populated `tool_calls`) on
the same prompts. Hermes Agent stopped wedging.

## Decision
The compose `command:` does **not** hardcode parsers as a global
default. Parsers are part of the **per-model config**: when
`INFERENCE_MODEL` changes, the operator must also revisit
`--tool-call-parser` and `--reasoning-parser` in
`inference/docker-compose.yml`.

The default values shipped in compose are tuned for the default
model (`cyankiwi/Qwen3.6-27B-AWQ-INT4`):

```
--tool-call-parser qwen3_xml
--reasoning-parser qwen3
```

## Lookup table — pick parsers per model family

| Model family                          | tool-call-parser   | reasoning-parser | Notes                                                       |
|---------------------------------------|--------------------|------------------|-------------------------------------------------------------|
| Qwen3 / Qwen3.5 / Qwen3.6 (Instruct)  | `qwen3_xml`        | `qwen3`          | XML-tagged tool calls; `<think>` reasoning block.           |
| Qwen3-Coder                           | `qwen3_coder`      | `qwen3`          | Different tool format from chat variant.                    |
| Qwen2.5 Instruct                      | `hermes`           | (none)           | Pre-reasoning era. `hermes` parser handles the format.       |
| Llama 3 / 3.1 / 3.3 Instruct          | `llama3_json`      | (none)           | JSON tool calls, no `<think>`.                              |
| Llama 4                               | `llama4_pythonic` or `llama4_json` | (none) | Two tool-call dialects; check the specific checkpoint.      |
| Mistral / Mixtral Instruct            | `mistral`          | (none)           | Mistral-style tool tokens.                                  |
| DeepSeek-V3 / V3.1 / V3.2             | `deepseek_v3*`     | `deepseek_r1`    | Match the version suffix; reasoning parser is shared.       |
| DeepSeek-R1 / distills                | `deepseek_v3` or `pythonic` | `deepseek_r1` | Pure reasoning model; `<think>` block is mandatory.         |
| Granite                               | `granite` / `granite4` | (none)       | IBM Granite chat models.                                    |
| Gemma 4                               | `gemma4`           | (none)           | Google Gemma 4.                                             |
| GLM 4.5 / 4.7                         | `glm45` / `glm47`  | `glm45`          | Reasoning parser shared across versions.                    |
| Kimi K2                               | `kimi_k2`          | (none)           | Moonshot AI.                                                |
| MiniMax / MiniMax-M2                  | `minimax` / `minimax_m2` | (none)     |                                                             |
| Phi-4-mini                            | `phi4_mini_json`   | (none)           |                                                             |
| Hermes finetunes (NousResearch)       | `hermes`           | depends on base  | Parser named after the *format*, not after Hermes Agent.    |

Run `vllm serve --help=tool-call-parser` and
`vllm serve --help=reasoning-parser` inside the running container to
see the live list — vLLM picks up new parsers between releases.

## Caveat: name collision
The parser called `hermes` is named after the **NousResearch Hermes
finetune lineage** (its tool-call output format). It is not named
after **Hermes Agent**, the laptop client harness our operator drives
benchmarks from. They share a name. The parser does not care which
client sends the request; the client does not care which parser
extracts the call. They're independent layers.

## Diagnostic table — symptoms of a parser mismatch

| Symptom on the agent client                          | Likely cause                                                        |
|------------------------------------------------------|---------------------------------------------------------------------|
| `tool_calls: []` and tool description in `content`   | Wrong `--tool-call-parser` for the model.                           |
| Dangling `</think>` in `content`                     | `--reasoning-parser` not set or wrong family.                       |
| Chain-of-thought in `content`                        | `--reasoning-parser` not set, or model emitting non-`<think>` reasoning markup. |
| HTTP 400 `'auto' tool choice requires …` on tools[]  | `--enable-auto-tool-choice` missing.                                |
| Agent silently wedges after 2-4 turns                | Parser-mismatch + agent's expectation of well-formed `tool_calls[]`. Logs in vLLM look 200; client side stalls. |
| `Content-Type: text/event-stream` ends prematurely   | Partial JSON tool args from a stale/unsuited parser.                |

## Consequences

**Positive.**
- Acknowledges that "OpenAI-compatible" is a leaky abstraction across
  open-weight models. The compatibility comes from the parser layer,
  not the model.
- Forces the operator to pause and adjust parsers when swapping
  models, rather than discovering misbehavior through downstream
  agent wedges.

**Negative / accepted.**
- One more variable to manage on each model swap.
- The lookup table will rot; vLLM ships new parsers and renames
  existing ones between releases. Live `--help=tool-call-parser` is
  the source of truth, not this ADR.

## Alternatives rejected
- **Use `--tool-call-parser auto`.** No such option exists. vLLM
  requires an explicit name.
- **Strip parser from compose, let vLLM run without one.** Then
  every request with `tools:[...]` returns HTTP 400. Worse than
  even a misconfigured parser — at least the latter sometimes works.
- **Pick the most lenient parser globally.** No such parser
  exists; `qwen3_xml` will produce nonsense on Llama tool calls and
  vice versa.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain (OKRs) inherited from the lab's AGENTS.md.
