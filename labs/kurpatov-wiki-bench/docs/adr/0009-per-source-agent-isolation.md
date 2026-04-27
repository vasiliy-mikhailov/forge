# ADR 0009 — Per-source agent isolation via Python SDK orchestrator + DelegateTool

Status: **Superseded by [ADR 0010](0010-retrieval-augmented-dedup.md)** (2026-04-27)
Originally Accepted: 2026-04-26.

> Per-source agent isolation via Python SDK + DelegateTool was the right
> direction but DelegateTool is deprecated upstream (since openhands-tools
> 1.16.0; will be removed in 1.23.0). The orchestration shape adopted
> in production is Python-loop top-orchestrator with TaskToolSet — see
> ADR 0010 for the design that supersedes this one. The findings about
> single-agent attention ceilings and per-source isolation rationale
> below remain canonical reference; the implementation choices for
> tools/CLI are stale.

Supersedes: none.
Related: [ADR 0007](0007-labs-restructure.md), [ADR 0008](0008-model-registry.md), experiments [`D7.md`](../experiments/D7.md), [`D7-rev2.md`](../experiments/D7-rev2.md), [`D7-rev3.md`](../experiments/D7-rev3.md), skill [`openhands-sdk-orchestration`](../../.agents/skills/openhands-sdk-orchestration.md).

## Context

The bench harness for `kurpatov-wiki-bench` runs an OpenHands agent inside a Docker container. The skill (`benchmark` v2) defines a 12-step ritual the agent applies to each of 7 sources of module 005: extract transcript → load prior known claims → factcheck empirical claims via Wikipedia → write a structured `source.md` (frontmatter + 5 sections + claim markers + URL citations) → commit + push.

Three production runs across two experiments demonstrate a robust failure mode:

| run                              | sources clean / 7 | failure mode                                                |
| -------------------------------- | ----------------: | ----------------------------------------------------------- |
| D7 #1 (skill v2 baseline)         |              1/7 | bulk-action shortcut for sources 001-006 after source 000  |
| D7-rev2 #3 (4 fixes)              |              4/7 | killed at 16:31 elapsed; ritual was holding              |
| D7-rev2 #4 (5 fixes)              |              5/7 | clean exit_code=0 after source 000 self-verify; agent declared task done |

The pattern across all three: a single OpenHands agent processing all 7 sources in one session accumulates context, then either degrades (loses ritual discipline mid-run) or exits early (decides the task is complete). The five environment-level fixes applied in D7-rev2 (path bug, factcheck SSL, image wrappers, Cyrillic pin, fallback ladder) closed all known external distractions, yet the ceiling moved only from 1/7 to 5/7. With friction removed, the binding constraint is the single agent's per-source attention budget and self-determined "I'm done" signal at high context size.

D7-rev2.md§Post-Mortem records the empirical ceiling: **roughly 4–5 sources before single-agent context-budget reasoning collapses**.

## Spike findings (added 2026-04-26 afternoon, see `tests/synthetic-orchestrator/step1..5a_orchestrator.py`)

The original Proposed draft of this ADR named the OpenHands SDK CLI's `task` tool (in headless mode) as the chosen delegation mechanism. Spike testing falsified that:

- **The `task` tool is exposed in the headless CLI's tool loadout** with the schema `{description: str, prompt: str}` and the description "Launch a subagent to handle complex, multi-step tasks autonomously". Initial signal looked promising.
- **First failure**: invoking `task` produces `ValueError: Unknown agent 'general-purpose'. Available types: none registered.` — the bundled subagent presets at `<MEI>/openhands/tools/preset/subagents/{default,…}.md` are not auto-loaded by the CLI in `--task` mode.
- **Workaround**: place a project-level `<cwd>/.agents/agents/general-purpose.md` file (per directory conventions in upstream [agent-creator fallback.md](https://docs.openhands.dev/sdk/guides/agent-file-based)). This makes the type registered.
- **Second failure (blocking)** after the workaround: `RuntimeError: no running event loop` thrown from `task → start_task → _create_task → ... → mount → _register → _start_messages → create_task`. The headless mode does not initialise the asyncio event loop required for delegation. Reproducible in CLI versions 1.15.0 and 1.17.0.

The Python SDK pattern (used by upstream examples [25_agent_delegation.py](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/25_agent_delegation.py), [41_task_tool_set.py](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/41_task_tool_set.py), [42_file_based_subagents.py](https://github.com/OpenHands/software-agent-sdk/blob/main/examples/01_standalone_sdk/42_file_based_subagents.py)) is the canonical path and works first-try. Steps 0–5a of the synthetic-orchestrator TDD harness validated the pattern end-to-end:

| step | what                                                            | result                                                           |
|----: | ----                                                            | ----                                                             |
|    0 | pip install + import smoke                                     | ✓ openhands-sdk 1.17.0 + openhands-tools 1.18.1                 |
|    1 | DelegateTool + builtin default subagent → echo                 | ✓ first try                                                      |
|    2 | custom AgentDefinition `source-author` → echo                  | ✓ first try                                                      |
|    3 | sub-agent writes file at `source-N/output.md`                  | ✓ second try (path semantics — relative to workspace, not absolute) |
|    4 | sub-agent writes skill-v2-compliant source.md (synth fixture 1) | ✓ second try (parser bug — `bench_grade.py` regex required space in `[CONTRADICTS FACTS]` but skill v2 uses underscore; fix shipped) |
|    5 | orchestrator iterates 4 synth sources sequentially             | ✓ first try, 4/4 verified=ok, orchestrator events=14            |
|   5a | master prompt control-flow only, transcripts read from disk    | ✓ first try, 4/4 verified=ok, master prompt 1.1 KB regardless of transcript size |

## Decision

**Adopt orchestrator + per-source sub-agent architecture using the Python SDK** (`openhands-sdk` + `openhands-tools` packages, version 1.17.0 / 1.18.1) with `DelegateTool` and `AgentDefinition`. Concretely:

1. Bench `run.sh` invokes a Python orchestrator script (`labs/kurpatov-wiki-bench/orchestrator/run-d7-rev3.py` or similar) inside the Docker sandbox. The orchestrator is a `Conversation` driven by a `main_agent` whose only tool is `DelegateTool`.
2. The orchestrator's `send_message(...)` body is **control-flow only** — a master prompt (≤ ~1.5 KB) that lists per-source `(source_n, raw_path, target_path)` tuples and instructs `for each S: spawn → delegate → on failure stop`. Transcripts and source content are NOT inlined in the master prompt; sub-agents read transcripts from disk in their own (fresh) context.
3. Per-source sub-agent: a single `AgentDefinition` named `source-author`, registered via `agent_definition_to_factory`. Tools: `terminal`, `file_editor`, plus per-D7-rev3 helpers for fact-checking and known-claims discovery (Step 5c). `system_prompt` is the full skill v2 ritual scoped to one source.
4. Workspace layout: shared `/workspace` containing per-source subdirs `/workspace/source-{N}/` (created by orchestrator before each delegation). Sub-agent operates strictly inside its subdir.
5. Sub-agent's `finish` reply: literal `done` or `failed: <one-line-reason>`. Anything longer accumulates in orchestrator context.
6. Verification: orchestrator (or its Python wrapper) runs `bench_grade.py --single-source N --json` as **subprocess** (not as a tool inside the conversation). The verification JSON enters orchestrator state as a small structured observation (~200 tokens). On `verified=fail` the orchestrator stops the run — fail-fast.
7. Sub-agent owns retry of transient failures (Wikipedia 503, network blips) up to a small cap (e.g. 3 retries). Orchestrator does NOT retry.

The contract details for D7-rev3 specifically live in `docs/experiments/D7-rev3.md`. The how-to (gotchas, code snippets, links to upstream examples) lives in skill `.agents/skills/openhands-sdk-orchestration.md`.

## Consequences

### Positive

- **Per-source clean context.** Each delegated sub-agent gets a fresh `Conversation` from the SDK's perspective — its `state.events` starts empty. The empirical D7-rev2 single-agent ceiling (4–5 sources before degradation) is removed at the architectural level.
- **Orchestrator context bounded by design.** With master prompt ≤ 1.5 KB and per-source observation ≤ 200 tokens, orchestrator context grows by O(N) where N is sources, not by O(transcript_size × N). Synthetic Step 5a measured ~35 KB total events for 4 sources.
- **Verify by fact, not by claim.** `bench_grade.py --single-source-json` reads the artifact on disk and emits deterministic JSON. Orchestrator decides accept/fail based on that, not on sub-agent self-report. Aligns with the lab principle in `AGENTS.md`.
- **Single Python process, single LLM session, single Docker container.** No 7× container startup overhead (the bash-loop alternative would have incurred ~30s × 7 = ~3.5 min wasted). One `vllm-snapshot-start.json` and one `vllm-snapshot-end.json` per run.
- **Idiomatic OpenHands SDK usage.** Same pattern as upstream examples 25/41/42 — easier to extend later (parallel sub-agents, custom visualizer, agent_server-based remote workspaces, etc.) when needed.

### Negative / costs

- **Shared filesystem for sub-agents.** OpenHands' `DelegateTool` runs sub-agents in the same process as the orchestrator and shares the workspace directory. Per-source isolation is achieved by convention (subdirs + sub-agent prompt that forbids cross-source touching), not by sandboxing. A misbehaving sub-agent can in principle read or write outside its assigned subdir.
- **No parallelism in the basic design.** Sequential is the safe starting point. Parallel sub-agents would race on git push to the experiment branch and on shared `concept-index.json`. A future revision could use isolated branches per-source-N + final merge step; out of scope for D7-rev3.
- **Verification is a separate Python subprocess.** Orchestrator must call `bench_grade.py` between delegations; can't be a single `conv.run()`. The Python wrapper around `Conversation` interleaves `send_message → run → verify → next send_message`. This is fine, just a deviation from "one big conversation".
- **PyInstaller binary still in the image** for any tool-side or shell-side use. Mitigated by curl/python3 wrappers (forge:main `853bf2c`); see skill `openhands-sdk-orchestration` § PyInstaller leak.
- **`bench_grade.py` regex was buggy** before this experiment — the `CONTRADICTS_FACTS` marker required a space (`[CONTRADICTS FACTS]`) but skill v2 uses underscore (`[CONTRADICTS_FACTS]`). All prior D7 / D7-rev2 numbers for that one metric column are suspect; retro re-grade is a small (10 min) follow-up task. Fix in forge:main `1eae7b1`.

### Rejected alternatives

- **`task` CLI tool in `--headless` mode** — what the original Proposed draft of this ADR named. Falsified by spike: `RuntimeError: no running event loop` even after providing a `.agents/agents/general-purpose.md` to satisfy registration. The CLI's `--headless` path doesn't initialise the asyncio loop the `task` tool's delegation needs. Could be revisited if upstream fixes the headless event-loop init.
- **Bash-loop orchestrator** — `run.sh` launches 7 sequential `docker run openhands --headless --task <prompt>` invocations, one per source. Architecturally equivalent isolation guarantee. Rejected because: (a) loses the orchestrator-as-LLM-state-machine ergonomics; (b) ~30s × 7 = ~3.5 min container-startup overhead; (c) cross-source state (run-level summary, fail-fast control flow) has to live entirely in bash variables. Kept as documented fallback if Python SDK turns out to have a blocker we don't yet know about.
- **Single agent + raised `max_iterations`** — does not address the actual D7-rev2 #4 failure mode (agent decided task was done, called `finish` cleanly with exit_code=0). Bigger ceiling does not fix premature task-completion reasoning.
- **Per-claim sub-sub-agent (tree of subagents)** — each empirical claim its own micro-agent for factcheck + dedup. Rejected at this stage as premature optimisation. Revisit only if D7-rev3's single-level isolation proves insufficient.

## DelegateTool deprecation (added 2026-04-26 after Step 5d)

The decision above commits to `DelegateTool` (used in upstream example 25 and in our `step5{c,d}_orchestrator.py`). Mid-Step 5d we discovered:

- `DelegateTool` is **deprecated since openhands-tools 1.16.0**, scheduled for removal in 1.23.0. Replacement is `TaskToolSet` (upstream example 41).
- The 5-spawn cap that surfaced as a Step 5d failure is a `max_children=5` parameter on `DelegateTool.create()`, not a hard limit. We resolved by spawn-once-reuse pattern (per upstream example 41 with `animal_expert`); raising `max_children` would have been the alternative.
- `TaskToolSet` has no equivalent cap and per-call sub-agent state isolation by default — closer to "fire and wait" semantics. Migration is mechanical (replace 2-step spawn+delegate with single `task()` calls).

**Migration deferred** until production D7-rev3 stabilises and we have headroom. We are 5+ minor versions away from removal (currently on 1.18.1). DelegateTool's spawn-once-reuse pattern (Step 5d) handles our current synth scope. When migrating: each `task()` call is fresh — for our per-claim fan-out use case this is actually what we want (no leaking state between independent claims).

This ADR's Decision §1–§7 carry over unchanged on a TaskToolSet backbone — only the tool registration and per-claim delegation calls in source-author's prompt need rewriting.

Recorded in skill `.agents/skills/openhands-sdk-orchestration.md` under "DelegateTool is deprecated" and "DelegateTool spawn cap is max_children=5".

## Implementation pointers

Concrete code:

- `tests/synthetic-orchestrator/step5a_orchestrator.py` — minimum viable orchestrator (4 synth sources, master prompt 1.1 KB, sub-agent reads transcript from disk).
- `tests/synthetic-orchestrator/step5b_orchestrator.py` — DONE (forge:main `177f6ac`) — adds `get_known_claims.py` integration. 4/4 verified=ok, claims_REPEATED_sum=5.
- `tests/synthetic-orchestrator/step5c_orchestrator.py` — DONE — 3-level orchestration on 1 synth source. Per-claim fan-out: idea-classifier (pure-LLM) + fact-checker (terminal w/ factcheck.py). 1/1 verified=ok, 1 CONTRADICTS_FACTS caught, 3 real Wikipedia URLs.
- `tests/synthetic-orchestrator/step5d_orchestrator.py` — DONE — 3-level on 4 sources + concept-curator. Spawn-once-reuse pattern (per upstream example 41) to handle DelegateTool's max_children=5 cap. 4/4 verified=ok, REPEATED=5, CF=1, URLs=30, concepts=6.
- `tests/synthetic-orchestrator/step6_orchestrator.py` — pending — fail-fast policy: on verified=fail orchestrator stops without continuing to N+1.
- `tests/synthetic-orchestrator/step7_…` — pending — production module 005, all 7 sources.

Tooling:

- `evals/grade/bench_grade.py --single-source N --single-source-json` — verify-script contract for orchestrator. Emits the JSON shape spec'd in D7-rev3.md§Contract.
- `Dockerfile` — installs openhands-sdk + openhands-tools via pip in addition to the standalone CLI binary; mounts `prompts/` to `/task:ro` so launch prompts are reachable.
- `run.sh` — accepts `LAUNCH_PROMPT=…` env to choose which orchestrator-launch script to invoke.

Key references:

- Skill `.agents/skills/openhands-sdk-orchestration.md` — SDK gotchas the upstream docs do not cover explicitly.
- Upstream SDK examples 25 / 41 / 42.
- Upstream design principles: <https://docs.openhands.dev/sdk/arch/design>.
