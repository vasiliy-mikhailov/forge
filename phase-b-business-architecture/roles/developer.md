# Role: Developer

## Purpose

Implement the production code that realises an active R-NN
trajectory or a Phase F R&D experiment. Write the diff that
turns a hypothesis ("compact L1 hits trip-quality ≥ 0.20") into
a running mechanism, paired with the unit tests that lock the
contract. Realises the **Service operation** and **R&D**
quality dimensions of
[`../capabilities/forge-level.md`](../capabilities/forge-level.md)
inside whichever lab the work lands in (today: wiki-bench,
wiki-compiler, wiki-ingest, rl-2048).

This role does not author architecture. It does not author
requirements (Wiki PM does). It does not operate services in
production (DevOps does). It writes code, writes tests, runs
them, and ships diffs.

## Activates from

A Phase F experiment spec under
[`../../phase-f-migration-planning/experiments/`](../../phase-f-migration-planning/experiments/),
or a backlog entry under a lab's `docs/backlog.md` whose ICE rank
warrants a `## Implementation` section. Loading the role = loading
the spec/backlog file + the lab's `AGENTS.md` (per-lab Phase A-H
context) + the lab's `SPEC.md` if present.

## Inputs

- **The active spec** — Phase F experiment md or lab backlog row.
- **The lab the work lands in** (read + write): one of
  [`../../phase-c-information-systems-architecture/application-architecture/`](../../phase-c-information-systems-architecture/application-architecture/)`{wiki-bench, wiki-compiler, wiki-ingest, rl-2048}/`.
- **Existing tests** under `<lab>/tests/`.
- **Catalog rows** the spec cites
  ([`../../phase-requirements-management/catalog.md`](../../phase-requirements-management/catalog.md)).
- **Relevant ADRs** — lab-level (`<lab>/docs/adr/`) and forge-level
  (`../../phase-preliminary/adr/`).

## Outputs

- **Code diffs** in the lab — production source, helpers,
  fixtures.
- **Unit tests authored before the implementation** (TDD red →
  green; see `tests/synthetic/test_compact_restore.py` as a
  reference shape). Tests land in the same commit as the code
  they cover.
- **Sweep / measurement output** — when the spec defines a
  reward function, the developer runs the sweep and pastes the
  output into the spec's Execution log.
- **Commit messages** that name the closed R-NN row or the
  experiment id (`K2-R1`, `G2`, etc.) so the audit's P11
  cross-reference walk can trace work back to its driver.
- **Score-history rows** via `--log-scores` on the relevant runner
  when the change touches a tested module.

No prompt edits to wiki content (those are wiki-bench skill
files, owned by the Wiki PM via R-NN trajectories). No
schema-level changes (those go through the Wiki PM as an R-NN).
No deployment to production (DevOps territory). No ADR
emissions — the developer surfaces architectural questions to
the architect, who opens the ADR.

## Realises

- **Service operation** of `forge-level.md` — every shipped diff
  is a small operational improvement to a lab.
- **R&D** of `forge-level.md` — code that closes an experiment
  hypothesis adds to the corpus of falsified / confirmed
  knowledge.

## Decision rights

The role may decide, without architect approval:

- File / module structure inside a lab.
- Test fixture shape (synth vs e2e) per the cheap-experiment
  principle (architecture-principles.md P5).
- Refactor extent — as long as tests stay green and the diff is
  reviewable.
- Filler-pattern lists, regex specifics, threshold tuning —
  *inside* the variant space the spec defines.

## Escalates to architect

The role must NOT decide:

- Schema changes (frontmatter fields, section headers, claim
  markers, Compact-form sections) — those touch the lab's
  contract; surface as a question to the Wiki PM (who emits an
  R-NN row); architect decides.
- Cross-lab edits (a diff that touches > 1 lab in
  `phase-c-…/application-architecture/`). Each cross-lab edge
  is an architectural call.
- ADR-level decisions (containers vs. host execution; deploy
  topology; GPU policy).
- Adding a new top-level Goal (Phase A) or Capability (Phase B).
- Adding a new R-NN row to the catalog (Wiki PM's territory).

When in doubt: open a `Status: PROPOSED` note in the lab's
`docs/backlog.md`, do not implement, escalate.

## Capabilities (today)

- **OpenHands SDK** — runs the agent loop inside the lab's bench
  harness when iterating on skills (per the wiki-bench README).
- **Git** — commits to feature branches under
  `vasiliy-mikhailov` identity (per architecture-principles.md
  P1: single architect of record); pushes to `main` after the
  architect's review.
- **pytest / unit-test runners** — runs the lab's `tests/synthetic/`
  suite locally (CPU; no GPU needed for the cheap floor).
- **Sweep CLIs** — runs experiment sweeps the spec defines (e.g.
  `compact_restore/sweep.py`) and reports trip-quality numbers.
- **Score-history logging** — `--log-scores` on every runner the
  diff touches, so P21 (regression detection) has fresh data.

The role does NOT have:

- SSH access to mikhailov.tech (DevOps's territory).
- Direct write access to `kurpatov-wiki-raw` / `kurpatov-wiki-wiki`
  (those repos receive content via the wiki-ingest pusher and the
  Mac-side Cowork session, not via Developer commits).
- Authority to restart production containers (DevOps).

## Filled by (today)

Claude (Cowork desktop session) loaded with the activation
spec above + the lab's AGENTS.md. Tomorrow: any LLM agent
harness that can read md, edit code, run pytest, and commit
to git — the role definition is harness-agnostic on purpose.

## Tests

[`/tests/phase-b-business-architecture/roles/test-developer.md`](../../tests/phase-b-business-architecture/roles/test-developer.md)
— md test file codifying the role as agentic-behaviour test
cases (DV-NN). Cases use the When-Then-Set-expected-Arrange-Act-
Assert shape with a Reward function per [ADR 0015](../../phase-preliminary/adr/0015-verifiable-agent-rewards.md).

**Transitive coverage** (per ADR 0013 dec 9). Decision spec
[`../../phase-c-…/wiki-bench/SPEC.md`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/SPEC.md)
is exclusively activated by Developer in the bench-lab context;
the test-developer.md cases transitively cover the SPEC's
discipline rules.

Coverage target: every output category enumerated under
"Outputs" above is asserted by ≥ 1 test case.

## Measurable motivation chain
Per [ADR 0015](../../phase-preliminary/adr/0015-verifiable-agent-rewards.md)
decision point 1:

- **Driver**: Architect-velocity (every minute the architect
  spends writing production code is a minute not designing the
  next experiment) + R&D throughput (more falsifiable hypotheses
  closed per week).
- **Goal**: Quality (KR: pre_prod_share ≥ 0.95).
- **Outcome**: lab code matches its spec; tests pass; reward
  functions return numbers the audit can compare.
- **Measurement source**: runner: test-developer-runner (DV-NN cases; TDD discipline; PASS band ≥ 0.8)
- **Contribution**: runner: test-developer-runner pass rate (per-test-case aggregate); each PASS reduces a pre-prod bug class for the developer role; aggregate contributes to Quality KR pre_prod_share via the audit catch-rate side of the formula.
- **Capability realised**: Service operation + R&D
  ([`../capabilities/forge-level.md`](../capabilities/forge-level.md)).
- **Function**: Implement-feature-against-spec.
- **Role**: Developer (this file).
