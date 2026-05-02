# ADR 0026 — Recording-keep-rate metric per persona; pain ledger schema extended with Verdict + new/repetition split

## Status

Accepted (2026-05-02). Active.

## Motivation

Per [P7](../architecture-principles.md):

- **Driver**: ADR 0016's CI-1..7 cycle puts pain ledgers in front of the Wiki PM, but every ledger today treats each lecture as standalone — no signal about cross-lecture redundancy. Architect call: "parallel agents will not be capable of catching repetitions between lectures... let's make one more metric: which recordings will customer leave after lection, meaning it saves only information that he/she does not know already." The redundancy IS the customer's pain; without measuring it, the Wiki PM can't compress.
- **Goal**: TTS (KR: tts_share ≥ 0.30 per-use). Higher recording-keep rate = wiki actually saves time per lecture; lower = customer would skip / delete entire recordings as redundant.
- **Outcome**: pain ledger schema extended with three new sections — `## What was new`, `## What was repetition`, `## Verdict (KEEP / KEEP-PARTIAL / LEAVE)`. Customer-interview cycle becomes sequential per persona (each lecture's ledger reads prior ledgers in same persona's directory). New per-persona metric `recording_keep_rate = ledgers_with_KEEP / total_ledgers`.
- **Measurement source**: corpus-walk: WP-NN — count KEEP / KEEP-PARTIAL / LEAVE verdicts across 220 ledgers post-sweep.
- **Contribution**: this ADR introduces the keep-rate signal; contributes to TTS KR by exposing wiki redundancy (low keep-rate per persona = wiki has too much repeated content for that persona's level).
- **Capability realised**: Develop wiki product line.
- **Function**: Add-recording-keep-rate-metric.

## Context

Today's CI-1..7 cycle has each persona evaluate ONE lecture in isolation. Real customers don't read in isolation — they accumulate knowledge across the corpus. By lecture 30, they've seen the dominance-hierarchy story 4 times; that 4th time = LEAVE candidate. Without sequential cross-awareness, the cycle misses the redundancy signal.

Architect's framing: "PM job will be to find patterns there via deep interviews etc." — the keep/leave signal IS the pattern entry point. Cross-tabbing keep/leave verdicts across `theme × lecture × persona` surfaces the actual repetition map.

## Decision

### 1. Pain ledger schema extension

Three new sections appended at end of every ledger:

```
## What was new (vs. prior lectures + persona's pre-existing knowledge)
- <bullet list of NEW concepts/claims this lecture added from this persona's POV>

## What was repetition (already covered earlier)
- <bullet list of content already known from prior lectures or prior persona reading>

## Verdict
KEEP | KEEP-PARTIAL | LEAVE

<one-sentence rationale>
```

Verdict semantics:
- **KEEP** — lecture has enough genuinely new content the persona would retain it.
- **KEEP-PARTIAL** — some new + a lot of repetition; persona would skim-keep / extract notes only.
- **LEAVE** — overwhelmingly redundant from persona's POV; persona would delete after listening.

### 2. Sequential CI-2 processing per persona

Each lecture's ledger MUST read all prior ledgers in `kurpatov-wiki-wiki/metadata/customer-pains/<persona>/` BEFORE writing. The "What was new" sections of prior ledgers form the persona's accumulated knowledge.

Parallelism across personas remains valid (5 chains, one per persona); parallelism within a persona's chain is forbidden (sequential).

### 3. New per-persona metric: recording_keep_rate

Per persona:
```
recording_keep_rate = (count(KEEP) + 0.5 × count(KEEP-PARTIAL)) / total_ledgers
```

System-level: weighted mean across 5 personas.

Target: ≥ 0.50 (more than half of recordings deemed worth keeping per persona). Below 0.50 = wiki has serious redundancy problem; PM should compress.

### 4. New audit predicate P31 (queued — not enforced this commit)

Future P31: every CI-2 ledger has the three new sections + a Verdict in {KEEP, KEEP-PARTIAL, LEAVE}. Walks via post-sweep tooling. Enforced after the 220-session run completes.

### 5. PM job (CI-3..5) refined

CI-3 cross-tab is now extended:
- Pain themes × lecture × persona (existing).
- Verdict × lecture × persona (NEW). Surfaces lectures where ≥ 3 of 5 personas voted LEAVE — those are the compress / merge candidates.

### 6. ADR 0016's CI cycle — backwards compatibility

ADR 0016's CI-1..7 schema stays; this ADR extends CI-2's output schema (3 new sections) and CI-3's cross-tab dimensions (Verdict). Existing ledgers (Marina × 001/000) get migrated to new schema in same commit.

## Consequences

- **Plus**: redundancy signal becomes computable; PM can measurably compress wiki.
- **Plus**: per-persona keep-rate is a legible metric for product quality (low rate = "we're boring this persona").
- **Plus**: cross-persona LEAVE consensus identifies the universally-redundant lectures (highest-priority compression targets).
- **Minus**: sequential per-persona = slower than naive parallel. But correctness > speed (per architect call).
- **Minus**: late-sequence subagents read N-1 prior ledgers — context grows with N. By lecture 44, ~40K tokens of prior ledgers; per-subagent context ~80-100K.

## Invariants

- Pain ledgers MUST have all three new sections + Verdict; chains without violate the schema.
- Lectures within a persona's chain MUST be processed in lecture-folder-name sort order (consistent across personas).
- Keep-rate is computed post-sweep; not authored by hand into per-ledger files.

## Alternatives considered

- **Use a separate `knowledge_state.md` per persona, updated each iteration**. Considered. Rejected: ledgers ARE the state — "What was new" sections sum to knowledge. Single source of truth.
- **Have each agent process ALL 44 lectures sequentially within one context**. Rejected: 44 × 25K = 1.1M tokens, exceeds Sonnet's 200K context budget. Subagent-per-lecture-batch is the workable scale.
- **Boolean keep/leave only (no KEEP-PARTIAL)**. Rejected: real customers skim; the middle category captures "extract notes then delete the recording" behavior which is genuinely informative.

## Follow-ups

- **P31 enforcement** — walks every ledger for the three new sections.
- **`recording-keep-rate-report.py`** — counts verdicts across 220 ledgers; emits per-persona + system-level keep_rate.
- **CI-3 cross-tab tooling** — walks ledgers; emits `verdict × lecture × persona` matrix for the PM.
- **Marina's Step 0 ledger** — gets schema update in same commit (lecture 1 of her chain; "What was new" = all of it; "What was repetition" = none; Verdict = KEEP).
