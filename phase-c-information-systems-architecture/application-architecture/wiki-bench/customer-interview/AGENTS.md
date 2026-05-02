# wiki-bench / customer-interview lab

CI-2 driver for the [Wiki Customer interview cycle](../../../../../phase-requirements-management/wiki-customer-interview.md)
(per [ADR 0016](../../../../../phase-preliminary/adr/0016-wiki-customers-as-roles.md) + [ADR 0023](../../../../../phase-preliminary/adr/0023-okr-cascade-numerical-targets.md)).

## Status

**Step 0 PASSes** (commit `c08f872` in private repo `kurpatov-wiki-wiki`):
- 1 lecture × 1 persona = 1 pain ledger written.
- Format conformant; voice conformant; pain signal real.

**Sweep pending** API key configuration. 219 remaining sessions
(44 lectures × 5 personas − 1 done).

## Phase A — Architecture Vision

Realises [TTS Goal](../../../../../phase-a-architecture-vision/goals.md):
the customer-interview cycle measures pain points that drive wiki
quality improvements; high-quality wiki → reader saves time.

## Phase B — Business Architecture

Wiki Customer abstract role + 5 personas:
- [academic-researcher](../../../../../phase-b-business-architecture/roles/customers/academic-researcher.md)
  (Marina, 2337w, citation-hunter)
- [entry-level-student](../../../../../phase-b-business-architecture/roles/customers/entry-level-student.md)
  (Аня, 2697w, definition-hunter)
- [lay-curious-reader](../../../../../phase-b-business-architecture/roles/customers/lay-curious-reader.md)
  (Антон, 2699w, phone-burst reader)
- [time-poor-reader](../../../../../phase-b-business-architecture/roles/customers/time-poor-reader.md)
  (Антон-PM, 2696w, TL;DR scanner)
- [working-psychologist](../../../../../phase-b-business-architecture/roles/customers/working-psychologist.md)
  (Анна, 2699w, "could-I-use-this-Tuesday" practitioner)

## Phase C — Information Systems Architecture

This lab. Drives the CI-2 step of the cycle.

## Phase D — Technology Architecture

Claude API (per architect call: NOT Blackwell vLLM, since K1 v2's
"wiki published itself in English" postmortem showed vLLM is fragile
on language/voice contracts).

## Phase E — Opportunities and Solutions

Sweep launch:
1. Configure `ANTHROPIC_API_KEY` env var.
2. Dry-run preview: `python3 run-ci-2.py --persona academic-researcher --module 001 --lecture-index 0 --dry-run`
3. Resumable full sweep: `python3 run-ci-2.py --all-personas --modules 000,001`
   (Skips already-done ledgers via the `out.exists()` check; safe to
   re-run after partial.)

Estimated cost: ~$12 total (Sonnet 4.6, 220 × ~15K input + ~700 output tokens).
Estimated wall time: ~10-15h serial; faster with rate-limit-aware concurrency.

## Phase F — Migration Planning

Per architect call: sweep on return when API key configured. Output
lands in private repo `kurpatov-wiki-wiki/metadata/customer-pains/<persona>/`
per [ADR 0018](../../../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md)
privacy boundary.

## Phase G — Implementation Governance

Resumable + incremental — interrupt-safe. Each session writes one
file; the driver skips files that already exist. So a `Ctrl-C` mid-sweep
loses at most one in-flight session.

## Phase H — Architecture Change Management

Pain ledgers feed CI-3 cross-tabulation (Wiki PM walks the 220 ledgers
post-sweep) → CI-4 problem identification → CI-5 R-NN row emission to
forge `catalog.md`.

## Measurable motivation chain

Per [P7](../../../../../phase-preliminary/architecture-principles.md):

- **Driver**: 5 personas × 44 lectures = 220 customer pain ledgers
  (per ADR 0016 cycle); manual via 5 chat-driven sessions = 220
  architect interventions. Need autonomous run.
- **Goal**: Architect-velocity (KR: ≤ 20 execution failures / 30-day rolling).
- **Outcome**: one-command `run-ci-2.py --all-personas --modules 000,001`
  produces all 220 ledgers in private repo without architect prompting
  per session; resumable; cost-bounded; output schema-conformant.
- **Measurement source**: lab-tests: WB (wiki-bench smoke) + corpus-walk:
  WP-NN (per-lecture coverage check post-sweep).
- **Contribution**: lab-tests: WB pass rate (4/4 = 1.000 today) — one
  more lab-domain prevented; sweep adds 220 pain ledgers to the
  customer-interview cycle (CI-3..5 then turns these into R-NN
  trajectories); contributes to A-V KR by automating what would
  otherwise be 220 architect-prompted sessions.
- **Capability realised**: Develop wiki product line ([../../../../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md](../../../../../phase-b-business-architecture/capabilities/develop-wiki-product-line.md)).
- **Function**: Run-CI-2-customer-reading-pass.
- **Element**: this lab (`run-ci-2.py` driver + this AGENTS.md).
