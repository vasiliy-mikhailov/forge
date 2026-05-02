# ADR 0026 — Per-persona cumulative knowledge ledger + would_skip_share metric for cross-lecture redundancy

## Status

Accepted (2026-05-02). Active.

## Motivation

Per [P7](../architecture-principles.md):

- **Driver**: ADR 0016 set up the CI-1..7 customer-interview cycle
  with 5 personas × 44 lectures = 220 pain ledgers. My initial
  dispatch plan was 11 parallel agents, each handling 4 lectures ×
  5 personas. Architect call: "parallel agents will not be capable
  of catching repetitions between lectures." Correct — each agent
  sees only its 4-lecture window; cross-lecture redundancy patterns
  (e.g. Курпатов repeats Foucault three times across the course)
  are invisible to a 4-window agent. The wiki's TTS value depends
  precisely on detecting and compressing this redundancy — so the
  metric the wiki most needs is the one parallel-batched agents
  cannot produce.
- **Goal**: TTS (KR: tts_share ≥ 0.30 per-use). The would_skip_share
  metric directly feeds tts_share computation (a wiki version that
  drops would-skip content saves the reader the redundant time).
- **Outcome**: each persona accumulates a per-persona knowledge
  ledger across the lecture sequence; each per-lecture pain ledger
  reports a `would_skip_share` (0.0-1.0) plus cross-references to
  the prior lectures where each repeated idea first appeared; CI-3
  Wiki PM cross-tabulates redundancy patterns for the deep-interview
  step (CI-4 problem identification).
- **Measurement source**: corpus-walk: WP-NN per-persona
  redundancy aggregate (mean of per-lecture would_skip_share
  values; pending CI-2 sweep completion).
- **Contribution**: this ADR introduces the would_skip_share metric
  + per-persona knowledge ledger schema; once the CI-2 sweep
  completes, the resulting per-persona redundancy maps feed Wiki PM
  CI-3..5 cross-tab → R-NN row emission for compress-by-redundancy
  experiments → directly contributes to TTS KR.
- **Capability realised**: Develop wiki product line.
- **Function**: Add-cumulative-knowledge-and-skip-metric.

## Context

The K2 (compact-restore) experiment in Phase F already addresses
WITHIN-lecture redundancy (Air bucket — fillers, discourse markers,
verbose asides). What it doesn't address: BETWEEN-lecture
redundancy (Курпатов restating the same conceptual frames across
multiple lectures in the same module).

The customer-interview cycle exposes between-lecture redundancy
through the persona's reading experience: Marina (academic-
researcher) reading lecture 12 thinks "wait, didn't he cite
Foucault the same way in lecture 3 and again in lecture 7?". A
per-lecture pain ledger that doesn't note this loses the signal.

A naïve fix: have ONE agent process all 44 lectures sequentially
for one persona. Per-agent context = 44 × ~25K + persona +
cumulative knowledge = ~1.3M tokens. Doesn't fit in any single
agent's context budget (Sonnet 4.6 = 200K). Hence:

## Decision

### 1. Per-persona knowledge ledger

Each persona maintains a single cumulative ledger at:

```
kurpatov-wiki-wiki/metadata/customer-pains/<persona>/__knowledge.md
```

Structure (append-only across lectures):

```markdown
# Knowledge ledger — <persona>

Cumulative summary of what this persona has learned across the
lecture sequence. Updated after each lecture's pain ledger lands.
Read by the next chunk's CI-2 invocation to detect cross-lecture
repetition (per ADR 0026 § Decision 2).

## After lecture 001/000 (lecture #1)

**Concepts now known**: <bullet list, 5-15 items>
**Authors / works now known**: <bullet list, 3-10 items>
**Methods / models now known**: <bullet list, 2-8 items>
**Курпатов's СПП framing**: <2-3 sentences>

## After lecture 001/001 (lecture #2)

**New concepts (not in prior list)**: <bullet list>
**Repeated from prior**: <bullet list with references to lectures>
...
```

Updated by each chunk-agent at end of run; read by next chunk-agent
at start.

### 2. Pain ledger schema extension

Each per-lecture pain ledger gains TWO new sections:

```markdown
## Would-skip share

`would_skip_share`: <0.00–1.00>  (estimated fraction of source the
persona would skim past as already-known from prior lectures or
general background)

Lecture #N for this persona; prior knowledge basis: see
`__knowledge.md` for accumulated state.

## What I would skip (cross-lecture repetition)

| Topic / claim | First seen in | This lecture's segments | Notes |
|---|---|---|---|
| Foucault on social institutions | 001/000 (seg 45-46) | seg 78-80 | repeated at same depth; could compress to 1-line cross-link |
| Сеченов's "behaviour" definition | 001/000 (seg 430-435) | seg 195-200 | partly extended (new context); keep extension only |
| ... | ... | ... | ... |
```

For lecture #1 of any persona, `would_skip_share = 0.00` and the
table is empty (no prior lectures).

### 3. CI-2 driver: sequential per persona, parallel across personas

`run-ci-2.py` updated:
- Lectures within a persona MUST run sequentially (ledger N reads
  knowledge ledger updated by ledger 1..N-1).
- Personas run independently (5 parallel streams).
- Each invocation can process a chunk (e.g. 5 lectures); next
  chunk reads the now-updated knowledge ledger.

For Cowork-mode dispatch (no API key), spawn 5 parallel agents per
chunk (one per persona); each agent handles ~5 sequential lectures
maintaining its persona's `__knowledge.md`. Round 1 covers lectures
0-4 × 5 personas = 25 ledgers; round 9 covers lecture 40 × 5 = 5
ledgers. Total: ~9 rounds × 5 personas = 45 agent invocations.

### 4. Aggregated metrics for CI-3 cross-tabulation

After all 220 ledgers land, Wiki PM's CI-3 reads the
`would_skip_share` values to produce:

- **Per-lecture redundancy index** = mean(would_skip_share across
  5 personas). High → lecture is mostly recap; candidate for
  aggressive compression.
- **Per-persona corpus redundancy** = mean(would_skip_share across
  44 lectures). High → corpus is repetitive for this reader;
  wiki should ship a heavily-condensed per-persona view.
- **Repetition theme map** = top-N most-repeated `Topic / claim`
  rows across all 220 ledgers. This is the Wiki PM CI-4 deliverable
  — concrete redundancy themes for CI-5 R-NN row emission.

### 5. New citation type `corpus-walk: WP-NN-redundancy`

ADR 0019's citation table gains a row:

| `corpus-walk: WP-NN-redundancy` | Per-persona redundancy aggregate from CI-2 sweep | `goals-report.py --metric redundancy` (queued) |

For chains that contribute to the cross-lecture-redundancy
measurement (this ADR; the CI-2 lab; future compress-by-redundancy
experiments).

### 6. Parallel-batched approach DEPRECATED for CI-2

The 11-batches-of-4 approach (sketched in commit message of
`52c31c7`) is deprecated per architect call. CI-2 driver enforces
the per-persona-sequential constraint; any future parallel
dispatch MUST be along the persona axis only.

## Consequences

- **Plus**: would_skip_share captures a metric the wiki's TTS value
  most depends on (compression of redundancy). Without it, the
  pain ledgers report only within-lecture pain, missing the
  between-lecture repetition signal.
- **Plus**: per-persona knowledge ledgers double as per-persona
  curriculum maps (what this persona learned by lecture N) — useful
  for the wiki's per-persona reading guides.
- **Plus**: 5-parallel-stream / sequential-within-persona dispatch
  fits agent context budgets (per-chunk agent: ~5 lectures × 30K =
  150K, within Sonnet 200K).
- **Minus**: ~9 sequential rounds (each round waits for the slowest
  agent before next). Total wall ≈ 9 × ~5min = 45min. Same order as
  the parallel-batched would have taken; just sequenced differently.
- **Minus**: would_skip_share is estimated by the persona-imitating
  agent, not measured directly (would need real-reader telemetry).
  Estimation noise — but useful directional signal per ADR 0023's
  "trend matters more than absolute value" framing.
- **Minus**: knowledge ledger format must stay stable across
  chunk boundaries; a chunk agent that mis-formats it breaks
  downstream chunks. Mitigation: schema in this ADR + a parser
  validator in goals-report.py.

## Invariants

- A new chunk-agent invocation that doesn't read its persona's
  `__knowledge.md` BEFORE writing pain ledgers = process violation.
- A pain ledger landing without `**Would-skip share**` section =
  P31 FAIL (queued — see follow-up #1).
- The knowledge ledger per persona is the source of truth for
  what's been said-so-far; no cross-persona knowledge sharing
  (each persona has independent prior-knowledge state).

## Alternatives considered

- **Single shared knowledge ledger across all personas**.
  Rejected: blurs persona-specific perception of redundancy.
  Marina notices repeated citation; Аня notices repeated jargon;
  Антон-PM notices repeated TL;DR-able structure. Different
  redundancies per persona.
- **Auto-detect redundancy by lexical / semantic similarity
  (no agent reading)**. Considered. Useful as a cross-check
  layer (and the K2 measure-corpus-recall.py harness already does
  shingle overlap). Doesn't replace persona-imitating estimate
  because semantic similarity ≠ what a specific persona perceives
  as "I already know this".
- **Skip the metric; only collect per-lecture pains**. Rejected
  per architect call.

## Follow-ups

- **P31 — Pain ledger schema conformance** (queued #1) — predicate
  walks all `kurpatov-wiki-wiki/metadata/customer-pains/<persona>/
  *.md`; verifies schema (Pains / Wins / Verdict / Would-skip
  share / What-I-would-skip table). FAIL if missing.
- **goals-report.py extension** (queued #2) — `--metric redundancy`
  walks all knowledge ledgers + would_skip_share values; emits
  per-lecture / per-persona / theme-map aggregates.
- **Wiki PM CI-3..5 driver** — automated cross-tab from the 220
  ledgers; currently planned as Wiki PM manual walk + R-NN emission.
- **Compress-by-redundancy experiment K3** — once the redundancy
  theme map is in hand, K3 builds a per-persona compressed wiki
  view that drops content with would_skip_share > threshold.
