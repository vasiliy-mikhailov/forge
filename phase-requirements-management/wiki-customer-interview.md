# Wiki customer interview cycle

The Wiki PM's **customer-development cycle**, complementary to
[`wiki-requirements-collection.md`](wiki-requirements-collection.md).
Where `wiki-requirements-collection.md` covers the architect-
side discovery (corpus walk, observation classification, R-NN
emission), this file covers the **customer-side** discovery:
how the [Wiki PM role](../phase-b-business-architecture/roles/wiki-pm.md)
gathers per-segment reader pain via a defined set of customer
personas (each filling the
[Wiki Customer role](../phase-b-business-architecture/roles/wiki-customer.md)),
cross-tabulates the signals, and turns them into R-NN rows.

Introduced by [ADR 0016](../phase-preliminary/adr/0016-wiki-customers-as-roles.md).

## When to walk

- A new lecture lands on `kurpatov-wiki-raw` (or a new module
  arrives) and the Wiki PM wants to know what's painful for
  each segment before authoring R-NN rows.
- A K-experiment closes (K2-R3 etc.) and the Wiki PM wants to
  measure whether per-persona pain dropped (loop-closure
  measurement).
- A new persona opens (Wiki PM proposes, Architect approves).
- A persona's pain pattern stops appearing — reconfirm or
  retire the persona.

## Activation

Loading this file activates the Wiki PM in customer-interview
mode. The role's `wiki-pm.md` notes both this file and
`wiki-requirements-collection.md` as activations.

## Steps

### CI-1. Pick a lecture under study

The Wiki PM picks one `<stem>` (raw.json + slides if available)
to interview the customers about. Default cadence: every new
lecture lands on `kurpatov-wiki-raw` triggers a CI-1..7 cycle;
re-runs after each K-experiment close.

### CI-2. Activate each customer persona

For each persona in
[`../phase-b-business-architecture/roles/customers/`](../phase-b-business-architecture/roles/customers/):

- Open a fresh Cowork session (or sub-Conversation).
- Load
  [`../phase-b-business-architecture/roles/wiki-customer.md`](../phase-b-business-architecture/roles/wiki-customer.md)
  + the persona file (e.g. `entry-level-student.md`).
- Provide the raw lecture (transcript + slides path).
- The customer reads the lecture in-character, produces a pain
  ledger at
  `phase-b-business-architecture/products/kurpatov-wiki/customer-pains/<persona-slug>/<lecture-stem>.md`.

The 5 personas (today): entry-level-student,
working-psychologist, lay-curious-reader, academic-researcher,
time-poor-reader.

### CI-3. Cross-tabulate the pain ledgers

The Wiki PM reads all 5 ledgers for the lecture and produces a
cross-tab:

| Pain | entry-level | working-psy | lay-curious | academic | time-poor |
|------|---|---|---|---|---|
| Selye attribution buried | mild | — | — | **blocking** | mild |
| Filler density | mild | mild | mild | — | **blocking** |
| (etc.) | | | | | |

**Rule of strength**: a pain reported by ≥ 2 personas is a
strong signal (likely a real wiki defect); a pain reported by
1 persona is a weak-but-real signal (worth capturing as a
persona-specific R-NN).

### CI-4. Wiki PM re-listens to the lecture

The PM listens / reads the raw lecture **once more** to
verify pain reports against ground truth. This catches LLM-
persona hallucination ("the customer reported a pain that
isn't actually in the lecture"). One re-listen per lecture
per cycle. Per architecture-principles.md P5, this is the
cheap-experiment hedge against fully-outsourced judgement.

If the re-listen finds the pain doesn't match the lecture, the
ledger entry gets a `[VERIFIED-FALSE]` annotation by the Wiki
PM. The persona's run is NOT discarded — recurring
verified-false patterns from a persona triggers a persona
re-spec (CI-7 follow-up).

### CI-5. Emit R-NN rows from verified pain

For each verified pain that has ≥ 2 persona votes:

- Wiki PM emits an R-NN row in
  [`catalog.md`](catalog.md) per `wiki-requirements-collection.md` S7.
- The Source cell now MAY include `customer:<persona-slug>` in
  addition to (or instead of) the Phase A goal references the
  row already cites.
- Status starts at `PROPOSED`; Architect approves → `OPEN`.

For persona-specific pain (1 persona vote), emit R-NN with
Status `PROPOSED-PERSONA-SPECIFIC`. The Architect decides
whether to ship a fix that serves only one segment.

### CI-6. Implementation team ships against R-NN

The standard handoff: Developer / Source-author / DevOps land
a fix per the R-NN. No customer is involved in this step.

### CI-7. Re-run CI-1..5 against the new compact form

After implementation lands (next K-experiment cycle), the Wiki
PM re-walks CI-1..5 with the *compact* output as the input.
Per-persona pain count should drop. This is the loop-closure
measurement:

| Metric | Before fix | After fix |
|--------|---|---|
| time-poor `blocking` count | N | N' |
| academic `blocking` count | M | M' |

A row R-NN is closed when its driving pain drops to 0
across all personas that originally reported it.

## Pain ledger format

One md file per persona per lecture at
`phase-b-business-architecture/products/kurpatov-wiki/customer-pains/<persona-slug>/<lecture-stem>.md`.

Format (each entry):

```
## Pain N — <one-line description>

- **persona**: <persona-slug>
- **lecture**: <stem>
- **timestamp / paragraph**: <e.g. 14:32 OR para #18>
- **severity**: blocking | moderate | mild
- **what hurt**: <2-3 sentences in persona voice>
- **what would have helped**: <persona's proposed fix, if any>
```

Append-only. A persona revisits a lecture by adding new entries
with a new timestamp prefix, not by editing prior entries.

## Customer-interview cycle as a measurement

The cycle IS a measurement instrument — it produces falsifiable
per-persona pain counts. Per ADR 0015 the cycle's reward
function:

- **forward measurement**: each persona's pain count per
  lecture decreases monotonically across K-cycles (`blocking`
  faster than `moderate` faster than `mild`) → the wiki is
  improving for that segment.
- **regression detection**: any persona's pain count INCREASES
  cycle-over-cycle on the same lecture → P21-class regression,
  surfaced in next audit.

## Tests

Per-persona test md (CU-NN cases) is queued. Today the cycle's
discipline is enforced by:

- **WP-NN runner** (which already covers the Wiki PM's S7 R-NN
  emission discipline; new requirement: every R-NN row whose
  Source cell mentions `customer:<persona>` traces to ≥ 1 pain
  ledger entry citing the same persona — to be added as WP-15+).
- **Audit predicate P23** (queued, ADR 0016 Follow-up): "every
  R-NN row triggered by customer pain cites the persona slug
  in its Source cell".
