---
name: openhands-sdk-orchestration
description: >-
  How we use the OpenHands Software Agent SDK for orchestrator + sub-agent
  isolation in `kurpatov-wiki-bench`. Captures non-obvious gotchas discovered
  via spike testing — things upstream docs do not call out explicitly.
  Reference when authoring orchestrator scripts, sub-agent definitions, or
  debugging delegation flows.
triggers:
  - orchestrator
  - sub-agent
  - subagent
  - delegate
  - DelegateTool
  - TaskToolSet
  - task tool
  - max_children
  - source-author
  - register_agent
  - register_tool
  - openhands sdk
  - AgentDefinition
  - file-based agents
  - 3-level orchestration
  - per-claim fan-out
---

# OpenHands SDK orchestration — bench-side gotchas

This skill captures findings discovered while implementing D7-rev3 (orchestrator + per-source sub-agent isolation) on the `kurpatov-wiki-bench` lab. Upstream docs are referenced rather than duplicated; only things we had to discover ourselves are written out.

## Always prefer the Python SDK over the headless CLI for delegation

The `openhands` standalone binary (`/usr/local/bin/openhands`, PyInstaller bundle, version 1.15.0–1.17.0 in our deployments) ships a `task` tool whose description is "Launch a subagent to handle complex, multi-step tasks autonomously". Looks promising. **Does not work** in our docker harness:

- First failure mode: `ValueError: Unknown agent 'general-purpose'. Available types: none registered.` — fixed by placing a file `{cwd}/.agents/agents/general-purpose.md` (per [agent-creator skill fallback.md](https://docs.openhands.dev/sdk/guides/agent-file-based) directory conventions).
- Second failure mode after that fix: `RuntimeError: no running event loop` thrown from inside Textual TUI widget mounting (`mount → _register → _start_messages → create_task`). The headless mode does not properly initialise the asyncio event loop required by the `task` tool's delegation machinery. Reproducible in versions 1.15.0 and 1.17.0.

Conclusion: write a Python script that uses `openhands.sdk` directly. `pip install openhands-sdk openhands-tools` (we run on Python 3.12), then follow the canonical pattern.

## Canonical orchestrator pattern

Adapted from [example 42 — file-based subagents](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/42_file_based_subagents.py) with modifications for our use case (sub-agent receives small task spec, reads bigger artifacts from disk).

```python
from openhands.sdk import (
    LLM, Agent, Conversation, Tool,
    register_agent, agent_definition_to_factory,
)
from openhands.sdk.subagent import AgentDefinition
from openhands.sdk.tool import register_tool
from openhands.tools import register_builtins_agents
from openhands.tools.delegate import DelegateTool, DelegationVisualizer

# 1. CRITICAL: register_builtins_agents() makes "default" / "code_explorer" /
#    "bash_runner" / "web_researcher" available. Without it the agent that
#    tries to delegate to those types gets "Available types: none registered".
register_builtins_agents()

# 2. Custom subagent — declarative, no factory function needed
source_author = AgentDefinition(
    name="source-author",
    description="…",
    tools=["terminal", "file_editor"],
    system_prompt="""…""",
)
register_agent(
    name=source_author.name,
    factory_func=agent_definition_to_factory(source_author),
    description=source_author,           # passes the AgentDefinition itself
)

# 3. Make the delegate tool callable by the orchestrator
register_tool("DelegateTool", DelegateTool)

llm = LLM(model="openai/qwen3.6-27b-fp8", api_key="…", base_url="…")
main_agent = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
conv = Conversation(
    agent=main_agent,
    workspace="/tmp/orch-ws",            # shared filesystem with subagents
    visualizer=DelegationVisualizer(name="Orch"),
)
conv.send_message(master_prompt)
conv.run()
```

Reference SDK examples — read these once, all three are short:

- [25_agent_delegation.py](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/25_agent_delegation.py) — the basic `register_agent` + `DelegateTool` pattern. Two subagents in parallel.
- [41_task_tool_set.py](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/41_task_tool_set.py) — `TaskToolSet` (the higher-level tool that bundles spawn + delegate + bash sub-agents). Uses Anthropic-flavoured "task" tool name.
- [42_file_based_subagents.py](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/42_file_based_subagents.py) — `AgentDefinition` + `agent_definition_to_factory` route. The closest match to what we do.

## Orchestrator context bloat — root cause and fix

### Mechanism

`Conversation.run()` drives the agent in a loop: each turn the LLM is sent the **full** `state.events` serialised as messages — system prompt + every prior event including the first user message. Append-only by default. So:

```
turn N input ≈ system_prompt + first_user_message + Σ (action_i + observation_i for i < N)
```

The first user message lives in the context **forever**. If you put 200K chars of transcript content in your `send_message(...)`, every subsequent LLM call by the orchestrator pays the cost — both in inference latency on a 27B model and in eaten context budget.

Empirically observed (synthetic 4-source TDD harness, Step 5 vs Step 5a):

| variant                                | master_prompt | orch events bytes | source coverage   |
| -------------------------------------- | ------------: | ----------------: | ----------------- |
| Step 5  — transcripts inline in prompt |  ~5,000 chars |             ~64K  | 4/4 verified=ok   |
| Step 5a — transcripts read from disk   |  ~1,134 chars |             ~35K  | 4/4 verified=ok   |
| projection to prod (7 × 30K transcripts inline) | ~250,000 chars | catastrophic | unable to fit |

### Fix — orchestrator master prompt is control-flow only

Master prompt format we converged on:

```
You are an orchestrator. Process the N sources below sequentially.
For each source S in [1, 2, ..., N]:
  1. DelegateTool spawn id='src{S}' agent_types=['source-author'].
  2. DelegateTool delegate tasks={'src{S}': 'Process source S=<S>. raw_path=<raw>. target_path=<target>. Follow your system_prompt.'}.
  3. If sub-agent reply starts with 'failed:', call finish with the reason.
  4. Otherwise proceed to next.

Per-source inputs:
  S=1: raw_path=raw/001.json, target_path=data/sources/.../001 ….md
  S=2: raw_path=raw/002.json, target_path=data/sources/.../002 ….md
  …

Do NOT do source-authoring yourself. Only orchestrate via DelegateTool.
```

Sub-agent receives the source index and paths only. It reads the actual transcript content from disk inside its own (fresh) context — `cat raw/001.json` via the terminal tool. Sub-agent context is fresh per delegate, so its bloat is not shared.

### Sub-agent's `finish` reply must also be tiny

The reply string from sub-agent appears in the orchestrator's `state.events` as part of the `DelegateTool` observation. Keep it to one of:
- `done`
- `failed: <one-line-reason>`

Anything longer (a JSON of metrics, a paragraph of explanation) accumulates linearly in orchestrator context. Verification of artifact happens **outside** the orchestrator's conversation, via subprocess, by reading the file on disk.

## Sub-agent workspace model

Per [example 25](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/25_agent_delegation.py) and the upstream `delegate_tool_description.j2` template: subagents inherit the orchestrator's workspace directory. They are not isolated containers — they share the filesystem with the orchestrator and with any sibling subagents.

For per-source isolation in our use case, the convention is **subdirectories under the shared workspace**: orchestrator (or its launch harness) creates `/<workspace>/source-N/` per source and instructs the sub-agent to only operate inside it. The sub-agent's `system_prompt` enforces "do not touch /workspace/source-*/ for other sources".

Note: file paths in tool calls are interpreted **relative to the workspace dir**, not as absolute Linux paths. A sub-agent told to write `/workspace/output.md` will create `<workspace_dir>/workspace/output.md` (a literal `workspace/` subdirectory inside the workspace). Use plain relative paths in prompts, e.g. `source-N/output.md`.

## File-based subagent directory conventions

Per the [agent-creator skill's fallback.md](https://docs.openhands.dev/sdk/guides/agent-file-based) (also embedded in the bundled `agent-creator` skill at `~/.openhands/cache/skills/public-skills/skills/agent-creator/references/fallback.md`):

| Priority | Path | Scope |
| --- | --- | --- |
| 1 | `{project}/.agents/agents/<name>.md` | project (primary) |
| 2 | `{project}/.openhands/agents/<name>.md` | project (secondary) |
| 3 | `~/.agents/agents/<name>.md` | user (primary) |
| 4 | `~/.openhands/agents/<name>.md` | user (secondary) |

Filename must equal the agent's `name` exactly (`name: code-reviewer` → `code-reviewer.md`). Place files **directly in `agents/`** — no further subdirectories. The bundled subagent presets (default = `general-purpose`, `code_explorer`, `bash_runner`, `web_researcher`) live inside the PyInstaller bundle; **the standalone CLI does not auto-load them** — that's why you also need `register_builtins_agents()` in Python orchestrator scripts.

## PyInstaller `LD_LIBRARY_PATH` leak in the standalone binary

Important when running the binary from a Docker image rather than from a Python install. The `openhands` PyInstaller bundle unpacks its bundled libs to `/tmp/_MEI<random>/` at startup and exports `LD_LIBRARY_PATH=/tmp/_MEI…:…` so its own bundled python finds them. Side effect: when the agent's `terminal` tool spawns shell commands, the bundled `LD_LIBRARY_PATH` is inherited. The bundled `libssl.so.3` (older OpenSSL) shadows system `libssl`, breaking:

- `/usr/bin/curl`: `version 'OPENSSL_3.2.0' not found (required by libcurl.so.4)`
- `/usr/local/bin/python3` urllib HTTPS: `<urlopen error unknown url type: https>` (because `_ssl` fails to load)

The agent panics, tries `LD_LIBRARY_PATH=""` workarounds manually, burns minutes of attention budget. We have observed this consume ~3–10 minutes wall time on every cold-start of D7-era runs.

**Fix in the bench Docker image** (`forge:main` `853bf2c`): install thin shell wrappers at `/usr/local/bin/curl` and `/usr/local/bin/python3` that strip `LD_LIBRARY_PATH` before exec'ing the real binary. Build-time smoke validates HTTPS works under simulated PyInstaller leak.

## Visualizer caveat — DelegationVisualizer prints to stdout

`DelegationVisualizer(name="…")` is great for interactive runs (rich panels of orchestrator vs subagent activity). For non-interactive bench runs we want JSON-structured output to a `events.jsonl`. The standalone CLI's `--json` flag does this; for our Python orchestrator wrapper, we either skip the visualizer or replace it with a custom one that emits to `state.events`.

For TDD synthetic runs the default visualizer is fine — easy to read in the log.

## DelegateTool is deprecated as of openhands-tools 1.16.0

`from openhands.tools.delegate import DelegateTool` (used in upstream example 25 and in our `step5{c,d}_orchestrator.py`) is **deprecated** since openhands-tools 1.16.0 and scheduled for removal in 1.23.0. The deprecation warning fires at import:

```
DelegateTool is deprecated. Will be removed in 1.23.0.
Use TaskToolSet instead.
```

The replacement is `from openhands.tools.task import TaskToolSet` — used in upstream [example 41](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/41_task_tool_set.py). Schema differences:

| aspect              | DelegateTool (deprecated)                                       | TaskToolSet (current)                              |
|---------------------|-----------------------------------------------------------------|---------------------------------------------------|
| schema              | two commands: `spawn` (id, agent_type) + `delegate` (id, task)  | single call: `task(description, prompt, subagent_type, resume?)` |
| state across calls  | sub-agent's `state.events` persists across delegations to same id | each `task()` is a fresh sub-agent unless `resume=<task_id>` |
| concurrency cap     | `max_children=5` parameter on `DelegateTool.create()`            | no equivalent cap; backed by `TaskManager`        |
| natural-language fit| more procedural (spawn then delegate)                           | one call per task — closer to "fire and wait"     |

**Migration plan** for `kurpatov-wiki-bench`: defer until production D7-rev3 stabilises and we have headroom. Both work in 1.17.0/1.18.1; we are 5+ minor versions away from removal. Migration is mechanical (replace 2-step spawn+delegate with single `task()` calls) and removes the spawn-once-reuse workaround needed for 5-cap.

When you do migrate: sub-agent state isolation **per call** is the simpler default (each `task()` is fresh) — no need to think about prior delegations leaking into next one's context. The trade-off is loss of "warm" sub-agent state across rounds; for our per-claim fan-out where each claim is independent, this is in fact what we want.

## DelegateTool spawn cap is `max_children=5` (parameter, not hardcoded)

When source-author tries to spawn its 6th sub-agent in a single Conversation it gets:

```
ConversationError: Cannot spawn 1 agents. Already have 5 agents, maximum is 5
```

This is `DelegateTool.create(max_children=5)`. To raise: instantiate the tool with a higher number when registering — but in our usage we instead apply the **spawn-once-reuse** pattern (used in upstream example 41 with the `animal_expert` agent across two rounds):

- At the start of source-author's workflow: spawn three sub-agents `classifier`, `factchecker`, `curator`.
- For each claim: `delegate` with all three task strings to those same ids.
- Sub-agents accumulate state.events across calls (small claim text per call, ≤5 calls per source). Acceptable bloat.

This pattern keeps spawn count at 3 (well under the 5 cap) regardless of how many claims a source has.

In TaskToolSet (the current API) this concern goes away — there is no per-conversation child cap, and each `task()` is fresh by default.

## 3-level orchestration validated empirically

D7-rev3 Step 5d (`tests/synthetic-orchestrator/step5d_orchestrator.py`) confirms a 3-level architecture works end-to-end on Qwen3.6-27B-FP8:

```
Top orchestrator (DelegateTool only)
    │  spawn id='src{N}', delegate 'process source N'
    ▼
source-author (terminal + file_editor + DelegateTool)
    │  spawn classifier + factchecker + curator (once)
    │  for each claim: delegate(classifier, factchecker)
    │  for each new concept: delegate(curator)
    ▼
[idea-classifier (no tools, pure-LLM)]
[fact-checker (terminal w/ factcheck.py)]
[concept-curator (terminal + file_editor)]
```

Measured on 4 synthetic sources × ~3 claims each:
- 4/4 sources verified=ok
- claims_REPEATED_sum = 5 (cross-source detection works through shared filesystem)
- claims_CONTRADICTS_FACTS_sum = 1 (fact-checker caught 1950-Pareto error)
- wiki_url_count_sum = 30 (every URL traceable to a real factcheck.py invocation in events.jsonl)
- concepts created = 6 (idempotent — concept-curator does not duplicate)
- top orchestrator: 22 events, ~37 KB total bytes
- wall time: ~13 min (vs 2-level Step 5b's ~3.5 min — 3-level overhead is the trade-off for per-claim isolation)

The 27B model sustains the behavioural complexity of 3-level delegation when:

- each level's prompt is narrowly scoped (idea-classifier prompt is ~250 chars; fact-checker ~400; source-author ~3 KB)
- each sub-sub-agent returns a single line (`NEW`, `REPEATED from <slug>`, `URL: ...`, `CONTRADICTS_FACTS: ... | <url>`, `concept <slug> ready`)
- source-author keeps its own state by appending to a small in-LLM scratchpad (claim list with markers + URLs accumulated in the assistant's reasoning, not in tool outputs)

## Two cost-calculation warnings to ignore

```
UserWarning: Cost calculation failed: This model isn't mapped yet.
  model=qwen3.6-27b-fp8, custom_llm_provider=openai. Add it here -
  https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json.
```

litellm doesn't know the price for our self-hosted qwen, so the SDK can't compute USD cost. Harmless. Same for the deprecation warning about `authlib.jose`.

## See also

- [SDK Design Principles](https://docs.openhands.dev/sdk/arch/design) — upstream conventions about immutability, statelessness, declarative configuration. Read once, reference when reviewing PRs that change agent/tool boundaries.
- [Sub-Agent Delegation guide](https://docs.openhands.dev/sdk/guides/agent-delegation) — full conceptual treatment.
- [File-based agents guide](https://docs.openhands.dev/sdk/guides/agent-file-based) — frontmatter fields and directory conventions.
- Local: `forge/labs/kurpatov-wiki-bench/docs/adr/0009-per-source-agent-isolation.md` — the architectural decision.
- Local: `forge/labs/kurpatov-wiki-bench/docs/experiments/D7-rev3.md` — the experiment using these patterns.
- Local: `forge/labs/kurpatov-wiki-bench/tests/synthetic-orchestrator/step{1..5,5a..5d}_orchestrator.py` — TDD progression demonstrating the patterns. Step 5b adds REPEATED detection; 5c introduces 3-level orchestration on 1 source; 5d extends to 4 sources + concept-curator.
- Local: `.agents/skills/tdd-on-synthetic-fixtures.md` — methodology for the progressive TDD that produced this skill's findings.
