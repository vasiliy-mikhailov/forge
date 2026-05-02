# ADR 0001 — server-side OpenHands harness, not laptop-side Hermes

## Status
Accepted (2026-04-25).

## Context
The `kurpatov-wiki-wiki/skills/benchmark/SKILL.md` skill describes
an autonomous agent task: process sources 000–006 of module 005,
author wiki articles + concept files, push commits to a per-model
branch. The first attempts ran the agent on the operator's macOS
laptop using the Hermes Agent CLI. That setup hit several blocking
problems:

1. **Cyrillic-pathed files broke the laptop's bash tool.** Quoted
   non-ASCII args triggered exact 60-second policy timeouts (`ls
   '../raw/data/Психолог-консультант/'` → `60.4s [error]`).
2. **`read_file` errored on Cyrillic paths** independently of the
   shell tool — appeared to be tool-internal path validation.
3. **HTTP between laptop and `https://inference.mikhailov.tech`**
   intermittently dropped mid-stream (`No response from provider
   for 285s`), forcing reconnect cycles.
4. **Context exhaustion before STEP 1.** Multiple sessions burned
   60–85% of context on retry noise (Cyrillic encoding errors,
   wrong cwd assumptions, `find` hanging on Cyrillic args) and
   wedged before the first source was authored.
5. **`delegate_task` subagent failed to fire** with `Stream stalled
   mid tool-call` — and recovery on retry failed too.

We tried mitigations: helper Python scripts to bypass shell
Cyrillic, server-side vLLM defaults to disable reasoning so
`max_tokens` doesn't get burned, locale env exports. None of them
fixed the underlying laptop-harness fragility.

## Decision
**Move the agent to a Docker container on the same server as vLLM,
using OpenHands in headless mode.**

Why this avoids the failure surfaces:

- Linux Docker has no Cyrillic-arg policy and no `read_file` path
  validation. Russian filenames are just bytes plus a UTF-8 locale.
- The agent talks to vLLM via the same `https://inference.mikhailov.tech`
  endpoint (so we keep exercising the public TLS path), but over
  the local network — RTT is sub-millisecond, no transcontinental
  drop window.
- OpenHands has documented headless mode (`--headless --json -t
  <task>`) emitting JSONL event traces. We capture those per-run
  for offline comparison.
- OpenHands has its own context window per run, separate from the
  operator's terminal session — exhaustion is not a persistent
  state.

## Why OpenHands specifically
Comparable to:
- **Hermes Agent (laptop)** — has the bugs we're fleeing.
- **Aider** — code-focused; doesn't model the multi-step authoring
  + git-push + concept-file-update workflow well.
- **SWE-agent** — academic, weaker tool ecosystem in 2026.
- **Roll-our-own thin agent loop** — feasible (call OpenAI API,
  exec shell, write files, loop) but reinventing OpenHands's
  evaluation harness is a week of work for diminishing returns.

OpenHands lands on:
- Headless mode is first-class (CI use case).
- OpenAI-compatible LLM config is first-class (`LLM_BASE_URL`,
  `LLM_API_KEY`, `LLM_MODEL`).
- Active development through 2026; v0.46+ stable.
- Built-in Docker-based sandbox — agent's tools execute in
  isolation, not on the host directly.

## Why not in forge
Considered: add a `bench-runner/` subsystem to forge alongside
`caddy/`, `mlflow/`, `inference/`, etc. Rejected because:

- forge already has 4–5 subsystems competing for the operator's
  attention; adding a 6th adds friction.
- The bench harness consumes forge as a black box; it doesn't
  deeply integrate (no shared mlflow tables, no shared compose
  network, no GPU coupling). A standalone repo expresses that
  loose coupling more honestly.
- Iteration on the harness happens at a different cadence from
  forge infrastructure changes. Decoupling repos lets each move
  independently.

## Consequences

**Positive.**
- All harness flake we spent multiple days fighting is gone:
  Cyrillic, HTTP timeouts, context exhaustion. The agent runs in
  a clean Linux Docker container with predictable behavior.
- Per-run artifacts (`runs/<run_id>/`) make cross-model
  comparison straightforward.
- The SSH-driven workflow (operator's laptop → server's `make
  bench`) is robust: a `make` invocation is a single TCP round
  trip, and the agent runs entirely on the server.

**Negative / accepted.**
- One more repo to keep clean.
- One more Docker image graph to keep up to date (OpenHands app +
  runtime sandbox).
- We lose the "what's happening in real time" feedback the
  laptop terminal provided. Compensation: tail the events.jsonl
  and stderr.log via `tail -f runs/<run_id>/events.jsonl`.
- Coupling to OpenHands. If OpenHands stagnates or breaks badly
  we'd have to swap it out — the `run.sh` interface should make
  that a one-evening migration to whichever harness wins.

## Reversibility
High. Removing this repo is a single `rm -rf`. Forking back to
laptop-side Hermes is no harder than pasting the launch prompt
into Hermes again — though we wouldn't want to.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain inherited from the lab's AGENTS.md.
