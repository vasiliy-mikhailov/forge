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

| Agent | File | One-line purpose |
|-------|------|------------------|
| Wiki PM | [`wiki-pm.md`](wiki-pm.md) | Own the requirements catalog for every product on the [Wiki product line](../products/wiki-product-line.md). |

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
- **References** — cross-links.

Match these headers when adding a file.
