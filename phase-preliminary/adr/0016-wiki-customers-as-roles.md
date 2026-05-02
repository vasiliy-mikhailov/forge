# ADR 0016 — Wiki Customers as ArchiMate Business Roles; customer-development cycle drives requirements

## Status

Accepted (2026-05-02). Active.

## Context

Through K2 (audit-2026-05-01p, q, and the Step 0 falsifier in
audit-2026-05-01r) the architect noticed two converging signals:

1. **The K2 algorithm work was over-specified by the architect's
   own intuition.** The K2 spec assumed L2 (cross-source surface
   dedup) was a viable saved-time path; the Step 0 probe falsified
   it (best 0.02% across 60 raw transcripts). The L2 hypothesis
   came from the architect, not from a reader saying "I keep
   re-reading the same passage."

2. **The actual dedup signal lives at the *customer experience*
   level, not the surface-text level.** A new lecture says the
   same things as the prior transcript + the prior slides + the
   prior recorded talk-itself (3 forms of the same content per
   source). Across lectures, Курпатов re-explains the same
   *concepts* in different words. The reader's pain is "I had to
   sit through this idea three times" — that's a customer-pain
   signal, not a regex finding.

Today's `phase-a/stakeholders.md` has 3 entries (Architect,
future operator, "End users — TBD"). The "TBD" is exactly the
hole this ADR closes. Without typed customer personas, the
Wiki PM is making decisions on behalf of an undefined audience —
and the K2 saved-time goal can't be measured against a real
reader.

The architect-side discipline is good (audit walks clean, role
formalisation under way). The product-side discipline is missing:
no customer-development loop, no segmented audience, no per-
segment pain catalogue.

## Decision

### 1. Wiki Customer is a first-class ArchiMate Business Role

A new role lives at
[`phase-b-business-architecture/roles/wiki-customer.md`](../../phase-b-business-architecture/roles/wiki-customer.md)
— *generic* customer role description (purpose, activation,
inputs, outputs, decision rights, tests, motivation chain). The
role is **consumer-side**, distinct from the producer-side roles
(Architect / Wiki PM / Auditor / Developer / DevOps / Source-
author / Concept-curator) which already exist.

### 2. Five named customer personas fill the role

[`phase-b-business-architecture/roles/customers/`](../../phase-b-business-architecture/roles/customers/)
holds one persona file per segment. The initial five:

| Persona                            | Reading mode                                    | Primary pain                                  |
|------------------------------------|-------------------------------------------------|-----------------------------------------------|
| **entry-level-student.md**         | Linear, builds from zero                        | Drowning in jargon, unsure what's load-bearing |
| **working-psychologist.md**        | Index-and-skim for clinical techniques          | Has to wade through pop-philosophy to find the technique  |
| **lay-curious-reader.md**          | Course-as-entertainment, dips in/out            | Wants the punch-line + 1 anchor concept; doesn't need full lecture |
| **academic-researcher.md**         | Cross-references against literature             | Needs primary-source attributions (Selye / Freud / Pavlov) explicit |
| **time-poor-reader.md**            | Has 5–10 minutes; wants maximum density         | Anything that's not the punch-line is filler |

Each persona file follows the established Phase B role template
(Purpose / Activates from / Inputs / Outputs / Decision rights /
Escalates to / Capabilities / Tests / Motivation chain).

### 3. Customers consume raw lectures via OpenHands

Each persona is filled by a Cowork session loaded with:
- The persona file (the "who am I").
- A raw lecture (transcript, slides, or talk-as-recording — see
  decision 5 below).
- An OpenHands tool repertoire (the same harness wiki-bench uses)
  for note-taking + annotation.

The customer-as-agent reads the raw lecture, forms an opinion on
**lecture problems** from their persona's perspective ("the Selye
attribution is buried 7 minutes in", "I had to skip 3 minutes of
filler before reaching the actual technique", etc.), and emits
those notes into a per-customer **pain ledger** (one md file per
persona per lecture) under
`kurpatov-wiki-wiki/metadata/customer-pains/<persona>/<lecture-stem>.md` (private repo per [ADR 0018](0018-privacy-boundary-public-vs-private-repos.md) — corrected after this ADR shipped).

### 4. Wiki PM runs a customer-interview cycle

A new process spec
[`phase-requirements-management/wiki-customer-interview.md`](../../phase-requirements-management/wiki-customer-interview.md)
extends the Wiki PM's activation set. Steps:

- **CI-1.** Wiki PM picks a lecture under study.
- **CI-2.** Wiki PM activates each customer persona (5 today)
  with the raw lecture; collects pain ledgers.
- **CI-3.** Wiki PM cross-tabulates pain reports — same complaint
  from ≥ 2 personas = strong signal; persona-specific pain = weak
  but real signal.
- **CI-4.** Wiki PM re-listens to the lecture itself (architect-
  velocity hedge: PM doesn't outsource judgement entirely; one
  re-listen catches LLM hallucinations in the pain ledger).
- **CI-5.** Wiki PM emits R-NN rows in
  [`catalog.md`](../../phase-requirements-management/catalog.md)
  citing the persona(s) that surfaced the pain. Each R-NN row's
  Source cell now MAY reference a persona slug
  (`customer:entry-level-student`) in addition to the existing
  Phase A goal references.
- **CI-6.** Implementation team (Developer + DevOps + Source-
  author + Concept-curator) ships against the new R-NN rows.
- **CI-7.** Wiki PM re-runs CI-1..5 against the new compact form
  to verify the pain dropped (closing the loop).

### 5. The dedup model is customer-pain-driven, not text-pattern-driven

K2-R1 → K2-R3 + Step 0 probed the wrong layer. The real dedup
opportunities, ranked by customer-pain salience, are:

- **Within-source dedup** (same lecture, multi-form): transcript
  + slides + talk-itself can all describe the same point three
  times. Customer pain = "this is the third paragraph that says
  the same thing." Mechanically detectable: paragraph-level
  semantic similarity inside one raw.json (or across raw + slides
  + transcript trio).
- **Cross-lecture concept repetition**: Курпатов re-explains the
  same concept across lectures. The Step 0 probe confirmed
  21.6% of the 51 concept-graph names appear by name in lecture
  A — each is a place where a definition-paragraph can become
  a `[concept](link)`. This was K2's L3 idea (validated).
- **Surface 5-gram dedup across raw transcripts**: falsified
  (0.02% best signal). Drop from the K2 spec.

K2 layers re-named accordingly:
- L1 (Air-strip)            → ✓ shipped
- L2 (was: cross-source surface dedup) → **deleted**
- L2-new (within-source multi-form dedup) → BUILD when raw
                                              triples land
- L3 (concept-graph link-out) → BUILD next (probe-validated)
- L4 (LLM-as-judge paraphrase tolerance) → if L3 doesn't reach
                                            0.50 trip-quality

### 6. Phase A stakeholders.md is no longer "TBD"

`phase-a-architecture-vision/stakeholders.md` is updated in the
same commit to enumerate the 5 customer personas as stakeholders.
The "End users — TBD" entry is deleted (per delete-on-promotion;
TBD is no longer the truth).

### 7. Kurpatov-wiki-team Collaboration grows to include Wiki Customer

The collaboration
[`phase-b-business-architecture/roles/collaborations/kurpatov-wiki-team.md`](../../phase-b-business-architecture/roles/collaborations/kurpatov-wiki-team.md)
adds the Wiki Customer role (collective — instantiated per
persona). Decision-rights matrix gains a row: "report a lecture
pain → Wiki Customer; emit R-NN from a pain → Wiki PM; ship
fix → implementation team."

## Consequences

- **Plus**: requirements emission has a customer-driven signal
  source, not just architect intuition. K2 (and every future
  wiki-product project) gets falsifiable customer-pain inputs.
- **Plus**: the dedup model is corrected — the Step 0 finding
  that L2-as-spec'd doesn't work isn't just a K2 setback, it's
  data that informs the new layer model.
- **Plus**: per-persona reading-speed + voice-preservation
  measurements become possible (each persona's pain ledger
  before/after compact = a per-segment trip-quality signal).
- **Minus**: more roles to maintain. Mitigated by treating
  personas as stable artefacts (re-walk only when a new wiki
  product opens or a persona's pain pattern stops appearing in
  ledgers).
- **Minus**: the customer-interview cycle (CI-1..7) adds latency
  to R-NN emission. Mitigated by running it asynchronously per
  persona (no blocking handshake).

## Invariants

- A Wiki Customer role NEVER edits architecture or wiki content.
  Customers READ + REPORT pain. The producer-side roles fix.
- The customer pain ledger is append-only — a customer revisits
  a lecture by adding a new dated entry, not by editing prior
  reports.
- Wiki PM MUST re-listen to a lecture before emitting R-NN
  triggered by customer pain (CI-4). One persona's hallucination
  never lands in the catalog unverified.
- The 5 personas are NOT exhaustive. Adding a new persona is a
  Wiki-PM-proposes / Architect-approves move (not a free Wiki PM
  emission).

## Alternatives considered

- **Skip personas; let the architect emit R-NN solo.** The
  status quo before this ADR. Falsified by K2: the architect's
  intuition put L2-surface-dedup on the spec when no customer
  was asking for it.
- **One generic "End user" role**, not five personas. Loses
  per-segment trip-quality measurement; loses the
  cross-tabulation in CI-3.
- **Use real human customers, not LLM-personas.** Right end-state
  but premature: the wiki has 2 source.md files; not enough
  surface area to recruit real readers. LLM-personas as
  scaffolding now; real-reader replacement when the wiki ships
  modules 000+001 in full per K1.

## Follow-ups

- Per-persona test md (CU-NN cases per persona) so each
  customer's pain ledger format becomes verifiable per ADR 0013.
- A `customer-interview-runner.py` that mechanically counts pain
  ledger entries + cross-tabulates per CI-3.
- Audit predicate P23: "every new R-NN row triggered by customer
  pain cites the persona slug in its Source cell".


## Motivation

Per [P7](../architecture-principles.md) — backfit:

- **Driver**: K2 Step 0 falsified architect-emitted L2
  hypothesis; without customer-driven signal, R-NN reflects
  intuition not pain.
- **Goal**: TTS at per-segment granularity.
- **Outcome**: 5 personas + Wiki Customer abstract role +
  CI-1..7 cycle. R-NN rows can cite `customer:<persona>`.
