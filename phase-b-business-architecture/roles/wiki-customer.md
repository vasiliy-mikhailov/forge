# Role: Wiki Customer (generic)

## Purpose

Read raw lecture material as a specific reader-segment persona,
form an opinion on what's painful or wasteful from that
persona's perspective, and emit a per-lecture **pain ledger**
the [Wiki PM](wiki-pm.md) cross-tabulates and turns into R-NN
rows. Realises the *consumer side* of the wiki product —
distinct from the producer-side roles (Architect, Wiki PM,
Auditor, Developer, DevOps, Source-author, Concept-curator)
which build the artefacts.

This role does not edit architecture, requirements, code, or
wiki content. It reads + reports.

## Composition

The Wiki Customer role is an **abstract role** — instantiated by
one of N persona files under
[`customers/`](customers/). Today's personas:

- [`customers/entry-level-student.md`](customers/entry-level-student.md)
- [`customers/working-psychologist.md`](customers/working-psychologist.md)
- [`customers/lay-curious-reader.md`](customers/lay-curious-reader.md)
- [`customers/academic-researcher.md`](customers/academic-researcher.md)
- [`customers/time-poor-reader.md`](customers/time-poor-reader.md)

A Cowork session loaded with this generic file + one persona
file = one Customer activation. Outputs land per-persona, never
mixed — cross-persona aggregation is the Wiki PM's job (CI-3 in
[`wiki-customer-interview.md`](../../phase-requirements-management/wiki-customer-interview.md)).

## Activates from

[`../../phase-requirements-management/wiki-customer-interview.md`](../../phase-requirements-management/wiki-customer-interview.md)
— specifically step CI-2 ("Wiki PM activates each customer
persona with the raw lecture; collects pain ledgers"). The
persona file the customer is filling sits alongside as the
*identity* the activation loads.

## Inputs

- **One raw lecture** under study — `raw.json` from
  `kurpatov-wiki-raw` (transcript), or the matching slides
  PDF, or the recorded talk-as-audio (when available).
- **The persona file** (entry-level-student.md, …) — the
  customer's reading-mode + pain signature + vocabulary.
- **OpenHands tool repertoire** (file_editor, web_search,
  task_tracker) — for note-taking + light research while reading.
- **The current published wiki state** (read-only access to
  `kurpatov-wiki-wiki/data/sources/` + `data/concepts/`) — so the
  customer can flag "I would have wanted this to link to a
  concept article" or "this lecture said the same thing as
  source X already."

## Outputs

- **One pain ledger** at
  `phase-b-business-architecture/products/kurpatov-wiki/customer-pains/<persona>/<lecture-stem>.md`.
  Per-persona, per-lecture, append-only. Format documented at
  the top of `wiki-customer-interview.md`.
- **Specific structural pains** — timestamped (or paragraph-
  index'd) complaints: filler that wasted time, definition
  that came too late, claim that lacked attribution, concept
  that should have been linked to existing concept.md, etc.
- **NO** R-NN emissions, NO code, NO wiki edits. The customer
  REPORTS — the Wiki PM EMITS.

## Realises

- Drives the **TTS** Goal (Phase A) at the per-segment level —
  a customer's pain ledger is the empirical basis for measuring
  whether a compact reduces THIS persona's reading time.
- **Reading speed** + **Voice preservation** + **Concept-graph
  quality** quality dimensions of
  [`../capabilities/develop-wiki-product-line.md`](../capabilities/develop-wiki-product-line.md)
  — by reporting where each dimension fails for the persona.

## Decision rights

The role may decide, without consultation:

- Whether a passage is painful for THIS persona (subjective by
  definition; that's the whole point).
- Which paragraph / timestamp to flag.
- Severity tags — `mild` / `moderate` / `blocking` per the
  ledger format.
- Whether to consult an external source during reading
  (web_search) — within the SKILL's tool budget.

## Escalates to (or hands off to)

- **Wiki PM** — the customer's pain ledger is the input to CI-3
  cross-tabulation. The customer NEVER decides whether their
  pain becomes an R-NN; that's Wiki PM's call after seeing all
  5 personas' ledgers + re-listening (CI-4).
- **The customer never escalates to the Architect.** Customer
  → Wiki PM → Architect is the only chain.

## Capabilities (today)

- **OpenHands SDK** — runs inside the wiki-bench harness's
  sandboxed Docker container.
- **file_editor** — writes the pain ledger to disk under
  `customer-pains/<persona>/<stem>.md`.
- **web_search** — bounded by the persona's reading-mode
  (academic-researcher uses it more than time-poor-reader).
- **Read-only access** to forge tree, `kurpatov-wiki-wiki`,
  and `kurpatov-wiki-raw` vault.

The role does NOT have:

- Authority to edit any wiki content, architecture file, or
  catalog row.
- Authority to load multiple personas in one Conversation
  (one persona = one identity = one ledger output stream).

## Filled by (today)

For each persona: a Cowork session loaded with this generic
role file + the persona file. Today the architect can fill
all 5 personas serially in one workday (each persona ~30 min
per lecture). Tomorrow: real human readers replace LLM-personas
once the wiki is shipping enough material to recruit readers
(per ADR 0016 Alternatives — current LLM-personas are
scaffolding).

## Tests

PENDING. Per-persona test md (CU-NN cases per persona) is a
follow-up: the runner verifies the pain ledger format,
sub-checks (≥ N pain entries, severity-tag presence,
timestamp/paragraph references valid), and over time the
regression-vs-prior-pain-ledger check.

Transitive coverage today: the Wiki PM's CI-3 cross-tabulation
walks every customer ledger; missing or malformed ledgers fail
the Wiki PM's WP-NN coverage measurement on the next walk.

## Measurable motivation chain
Per [ADR 0015](../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision point 1 + [ADR 0016](../../phase-preliminary/adr/0016-wiki-customers-as-roles.md):

- **Driver**: K2 Step 0 falsified the architect-emitted L2
  hypothesis. Without customer-driven pain signal, R-NN rows
  reflect architect intuition, not reader experience.
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: Each persona's pain ledger drops over successive
  K compact runs (K2 → K3 → ...). Per-persona trip-quality
  becomes measurable.
- **Measurement source**: customer-cycle: CI-1 (5 personas activated; CI-3..5 ledgers pending — band = pending until cycle runs against modules 000+001)
- **Contribution**: customer-cycle: CI-1..7 PASS rate (5 personas activated; cycle pending) — when cycle runs, pain-ledger throughput per persona feeds Quality KR via the Quality dimensions catalog.
- **Capability realised**: TTS + Reading speed + Voice
  preservation + Concept-graph quality — *as scored by the
  reader, not the architect*.
- **Function**: Read-as-persona-and-report-pain.
- **Role**: Wiki Customer (this file; per-persona realisation
  in `customers/<persona>.md`).
