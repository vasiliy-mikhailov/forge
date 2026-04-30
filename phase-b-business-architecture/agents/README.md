# Agents

Persona definitions for the LLM agents that execute within the
structure forge's architect designed. Each file specifies *what
this agent is for, what it consumes, what it produces, what it
may decide on its own, and what it must escalate*.

The split between architect and agents is described in
[`../org-units.md`](../org-units.md). Short version: architect
makes the structure (functional, declarative); agents make it
alive (operational, imperative). This folder is the agents side.

## Agents formalised today

| Agent | Persona | Tests | One-line purpose |
|-------|---------|-------|------------------|
| Wiki PM | [`wiki-pm.md`](wiki-pm.md) | [`wiki-pm-tests/`](wiki-pm-tests/) | Own the requirements catalog for every product on the [Wiki product line](../products/wiki-product-line.md). |

## When to add a new persona file

A new file lands here when *any* of these is true:

- An agent's decision rights become non-obvious — its actions
  routinely affect artefacts it doesn't own (e.g. a developer
  agent that edits prompts referenced by ADRs).
- A regression traces to absent guidance for the agent — the
  fix is to write the persona, not to patch the prompt that
  failed.
- A new agent is being introduced to forge for the first time
  and the architect wants its scope spelled out before it
  produces output.

Agents that are still only running occasional sessions without
the above pressures stay informal — the lab's `AGENTS.md` is
their guidance.

## Persona file shape

Every file in this folder uses the same headers:

- **Purpose** — what the agent is for, in one paragraph.
- **Activates from** — the canonical document the agent loads to
  enter persona (a process spec, a skill file, etc.).
- **Inputs** — what the agent consumes per session.
- **Outputs** — what the agent produces per session, where they
  land in the repo.
- **Realises** — which Phase B capability dimension(s) the
  agent's output realises.
- **Decision rights** — what the agent may decide on its own.
- **Escalates to architect** — what the agent must NOT decide.
- **Realised by (tooling)** — which AI tool / harness runs the
  agent today (Cowork, Claude Code, OpenHands, etc.).
- **Tests** — link to the agent's `<agent>-tests/` folder.
- **References** — cross-links.

Match these headers when adding a file.

## MD tests for agents (TDD discipline)

A persona file is aspirational prose until something can fail it.
Every formalised agent in this folder ships with a `<agent>-tests/`
folder of *MD tests* — pass/fail predicates over the agent's
outputs, written in markdown. Tests are authored *before* the
agent runs for the first time (TDD), stay `RED` until the agent's
output passes them, and either `GREEN` once it does or `STALE`
when evidence accumulates that the test was wrong.

The discipline mirrors per-lab `tests/` folders (e.g.
[`../../phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/))
but at the agent layer: code is verified by code, agent behaviour
is verified by md.

### MD test file shape

Every test file uses these headers:

- **`# T-<AGENT>-NN — <one-line title>`** — `T` for test, agent
  abbreviation (`WP` for Wiki PM, `WD` for a future developer
  agent, etc.), monotonic per agent.
- **Scenario** — Given / When / Then, prose. The Given is the
  fixture, the When is the action the agent takes, the Then is
  what the resulting artefact must look like.
- **Fixture** — links to the input(s): the persona file, the
  process / skill the persona activates from, the data files the
  agent reads. Small inline excerpts allowed; large fixtures
  reference paths.
- **Acceptance** — numbered list of testable predicates. Each
  predicate is phrased so a verifier can implement it as a
  function over `(fixture, output) → pass | fail`. Prose-only
  predicates ("reads naturally") are not in the catalogue — they
  are notes, not tests.
- **Run** — concrete steps a verifier follows. May be:
  *(a) mechanical* — regex / parse / numeric comparison,
  *(b) LLM-as-judge* — another agent (different persona) reads
  the output and answers a yes/no, or
  *(c) eye-read* — architect verifies. Prefer (a) where possible;
  (c) is a smell flag (something is not testable).
- **Status** — one of `RED` (not run, or last run failed), `GREEN`
  (last run passed against the current persona + fixtures),
  `STALE` (evidence the test was wrong; needs re-write before
  next run). Status updates are commits, not in-place edits — git
  history is the test log.
- **Coverage map** — which persona responsibilities and which
  capability quality dimensions this test exercises. Several tests
  may share a coverage entry; an entry with 0 tests is a coverage
  hole.

### Coverage

`md coverage` for an agent is the union of `Coverage map` entries
across all its tests, divided by the union of (persona
responsibilities ∪ capability quality dimensions the agent
realises). Targets:

- **L0** — no tests. (The agent is informal; persona stays
  prose-only.)
- **L1** — ≥ 1 test exists. (Some predicate has been written.)
- **L2** — every persona Output line has ≥ 1 acceptance predicate.
- **L3** — every capability quality dimension the agent realises
  has ≥ 1 test, AND every Decision-rights line has ≥ 1 test that
  exercises it.
- **L4** — every Escalates-to-architect line has ≥ 1 test that
  catches the agent failing to escalate.
- **L5** — runner exists; tests run mechanically on every
  catalog change.

Tracked per-agent in the agent's tests/README.md.

### Lifecycle

```
RED ──(persona drafted, fixtures attached)──▶ RED
RED ──(agent run, output passes acceptance)──▶ GREEN
GREEN ──(persona changed; rerun fails)──────▶ RED
GREEN ──(real artefact contradicts test)────▶ STALE
STALE ──(test re-written with rationale)────▶ RED
```

A test going `STALE` is the *expensive* signal — it means the
catalog was wrong and the persona drove the agent into a real
regression that the test missed. Each `STALE` event is logged in
the test file itself with a reference to the artefact that
exposed the gap.
