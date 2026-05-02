# Develop wiki product line — capability realisation

ArchiMate-vocabulary-faithful description of how the
[Develop wiki product line](develop-wiki-product-line.md)
Capability is realised today. Per [ADR 0014](../../phase-preliminary/adr/0014-archimate-across-all-layers.md)
+ [`../../phase-preliminary/archimate-language.md`](../../phase-preliminary/archimate-language.md):
every element below is a typed ArchiMate construct. Each
artifact reference is a path in the forge working tree (or a
sibling content repo); cross-references are live links the
audit's P11 walk verifies.

This file is a **synthesis** of the Capability's realisation
across all TOGAF phases — not a replacement for the
per-phase artifacts it cites. Re-walked when a new Role,
Collaboration, ADR, or Process is added (last walked
2026-05-02 at commit pending; see audit-2026-05-01s).

## 1. Strategy layer (ArchiMate §3.4)

The Capability `Develop wiki product line` decomposes from the
four forge-level Capabilities in
[`forge-level.md`](forge-level.md): R&D, Service operation,
Product delivery, Architecture knowledge management. Today
instantiated for the Product
[`kurpatov-wiki`](../products/kurpatov-wiki/). Eight
**Quality Dimensions** (per
[`develop-wiki-product-line.md`](develop-wiki-product-line.md)):
Voice preservation, Reading speed, Dedup correctness,
Fact-check coverage, Concept-graph quality, Reproducibility,
Transcription accuracy, Requirement traceability.

## 2. Motivation layer (ArchiMate §6)

**Drivers** *influence* **Goals** *aggregate* **Outcomes** that
*realise* the Capability:

- **Drivers** ([`../../phase-a-architecture-vision/drivers.md`](../../phase-a-architecture-vision/drivers.md)):
  time-spent-consuming-Russian-psychology-lectures;
  architect-velocity; token-count-bloat-in-operational-md;
  customer-pain (per-persona, per [ADR 0016](../../phase-preliminary/adr/0016-wiki-customers-as-roles.md)).
- **Goals** ([`../../phase-a-architecture-vision/goals.md`](../../phase-a-architecture-vision/goals.md)):
  TTS, PTS, EB, Architect-velocity.
- **Stakeholders** ([`../../phase-a-architecture-vision/stakeholders.md`](../../phase-a-architecture-vision/stakeholders.md)):
  Architect, future operator, 5 customer personas (filling the
  Wiki Customer Role).
- **Principles** ([`../../phase-preliminary/architecture-principles.md`](../../phase-preliminary/architecture-principles.md)):
  P1 single architect of record; P2 capability trajectories
  with delete-on-promotion; P3 containers-only execution; P4
  single-server deployment; P5 metric-driven action /
  cheap-experiment; P6 completeness over availability for
  compiled artifacts.
- **Requirements**: 15 active R-NN trajectories in
  [`../../phase-requirements-management/catalog.md`](../../phase-requirements-management/catalog.md)
  spanning Phase B (R-B-*) and Phase D (R-D-*).
- **ADRs** (6 active in [`../../phase-preliminary/adr/`](../../phase-preliminary/adr/)):
  0001 monorepo-flat, 0009 ssh-ControlMaster, 0013 md-as-source-
  code TDD, 0014 ArchiMate adoption, 0015 verifiable agent
  rewards (RLVR), 0016 Wiki Customers as Roles +
  customer-development cycle.

## 3. Active structure (Business + Application + Technology)

### 3.1 Business Roles (§4.1.1)

8 Roles *assigned to* the Capability (7 producer-side + 1
consumer-side abstract):

| Role | Realising Business Function | Artifact |
|---|---|---|
| Architect of record | Decide-and-own-the-architecture | [`../roles/architect.md`](../roles/architect.md) |
| Wiki PM | Discover-requirements (architect-side + customer-side) | [`../roles/wiki-pm.md`](../roles/wiki-pm.md) |
| Auditor | Walk-predicates-emit-findings | [`../roles/auditor.md`](../roles/auditor.md) |
| Developer | Implement-feature-against-spec | [`../roles/developer.md`](../roles/developer.md) |
| DevOps | Operate-host-and-services | [`../roles/devops.md`](../roles/devops.md) |
| Source-author | Compile-one-raw-into-one-source | [`../roles/source-author.md`](../roles/source-author.md) |
| Concept-curator | Curate-the-concept-graph-as-sources-arrive | [`../roles/concept-curator.md`](../roles/concept-curator.md) |
| Wiki Customer (abstract) | Read-as-persona-and-report-pain | [`../roles/wiki-customer.md`](../roles/wiki-customer.md) |

### 3.2 Business Actors (§4.1.1) filling the Roles

- `vasiliy-mikhailov` — fills Architect (P1 single architect).
- LLM agents (Claude / Cowork sessions / OpenHands) — fill
  Wiki PM, Auditor, Developer, DevOps, Source-author,
  Concept-curator.
- 5 personas under [`../roles/customers/`](../roles/customers/)
  — fill Wiki Customer:
  [`entry-level-student`](../roles/customers/entry-level-student.md),
  [`working-psychologist`](../roles/customers/working-psychologist.md),
  [`lay-curious-reader`](../roles/customers/lay-curious-reader.md),
  [`academic-researcher`](../roles/customers/academic-researcher.md),
  [`time-poor-reader`](../roles/customers/time-poor-reader.md).

### 3.3 Business Collaboration (§4.1.2)

[`../roles/collaborations/kurpatov-wiki-team.md`](../roles/collaborations/kurpatov-wiki-team.md)
aggregates the 8 Roles with a **disjoint decision-rights
matrix**; conflicts route to the Architect (P1).

### 3.4 Application Components (§4.2.1) and Application Services (§4.2.4)

| Component | Sub-components | Application Services exposed |
|---|---|---|
| [`wiki-ingest`](../../phase-c-information-systems-architecture/application-architecture/wiki-ingest/) | faster-whisper transcriber + lean pusher | audio-to-raw transcription; raw.json publication |
| [`wiki-bench`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/) | OpenHands SDK harness; `compact_restore/` | compile-source.md service; compact L1 service; recall-measurement service |
| [`wiki-compiler`](../../phase-c-information-systems-architecture/application-architecture/wiki-compiler/) | vLLM serving | OpenAI-compatible inference endpoint |
| [`rl-2048`](../../phase-c-information-systems-architecture/application-architecture/rl-2048/) | parallel R&D Lab | (out of scope for wiki Capability) |

### 3.5 Technology Layer (§4.4)

- **Node**: `mikhailov.tech` ([`../../phase-d-technology-architecture/architecture.md`](../../phase-d-technology-architecture/architecture.md))
  hosts everything (P4 single-server).
- **Devices**: NVIDIA RTX PRO 6000 Blackwell + RTX 5090.
- **System Software**: Caddy (TLS / HTTP mux per [ADR 0007](../../phase-g-implementation-governance/adr/0007-labs-restructure-self-contained-caddy.md));
  docker compose (P3 containers-only); OpenHands SDK; vLLM.

## 4. Behaviour (Business Processes — §4.1.3)

Five named Processes realising the Capability:

- [`wiki-requirements-collection`](../../phase-requirements-management/wiki-requirements-collection.md)
  — S1..S8 architect-side discovery (Wiki PM walks corpus,
  classifies observations into Substance/Form/Air, decomposes
  goals, emits R-NN).
- [`wiki-customer-interview`](../../phase-requirements-management/wiki-customer-interview.md)
  — CI-1..7 customer-side discovery (Wiki PM activates each
  persona, cross-tabulates pain ledgers, re-listens, emits R-NN
  with `customer:<persona>` Source cells).
- [`audit-process`](../../phase-h-architecture-change-management/audit-process.md)
  — Auditor walks 22 typed predicates (P1..P22) every ~5
  days; emits `audit-YYYY-MM-DD<suffix>.md` with FAIL / WARN /
  INFO findings.
- K2 R&D cycle ([`../../phase-f-migration-planning/experiments/K2-compact-restore.md`](../../phase-f-migration-planning/experiments/K2-compact-restore.md))
  — falsifier-first probe → TDD → RLVR sweep → architect call
  → trajectory promotion.
- [`process.md`](../../phase-requirements-management/process.md)
  — generic requirements-management cycle (R-NN lifecycle).

## 5. Passive structure (Data Objects + Artifacts)

### 5.1 Phase Preliminary

- Method + principles + repository + team artifacts under
  [`../../phase-preliminary/`](../../phase-preliminary/).
- 6 ADRs (0001, 0009, 0013, 0014, 0015, 0016).

### 5.2 Phase A (Architecture Vision)

- 5 Phase-A artifacts:
  [`vision.md`](../../phase-a-architecture-vision/vision.md),
  [`goals.md`](../../phase-a-architecture-vision/goals.md),
  [`drivers.md`](../../phase-a-architecture-vision/drivers.md),
  [`stakeholders.md`](../../phase-a-architecture-vision/stakeholders.md),
  [`principles.md`](../../phase-a-architecture-vision/principles.md).

### 5.3 Phase B (Business Architecture)

- 4 Capability artifacts under [`../capabilities/`](../).
- [`../products/wiki-product-line.md`](../products/wiki-product-line.md),
  [`../products/kurpatov-wiki/corpus-observations.md`](../products/kurpatov-wiki/corpus-observations.md)
  (30 Substance/Form/Air observations).
- 8 Role artifacts (above) + 5 persona artifacts + 1
  Collaboration artifact.
- 5 customer-pain ledger directories under
  [`../products/kurpatov-wiki/customer-pains/`](../products/kurpatov-wiki/customer-pains/)
  — today empty; first CI-1..7 cycle pending.

### 5.4 Phase C (Information Systems)

- 3 Lab roots (wiki-ingest / wiki-bench / wiki-compiler) +
  rl-2048.
- `compact_restore/` sub-component:
  [`compact.py`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/compact.py),
  [`restore.py`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/restore.py),
  [`filler_patterns.py`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/filler_patterns.py)
  (V1..V5),
  [`sweep.py`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/sweep.py),
  [`probe_overlap.py`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/probe_overlap.py),
  [`Dockerfile.k2-sweep`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/Dockerfile.k2-sweep),
  [`compose.k2-sweep.yml`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/compose.k2-sweep.yml).
- 30 pytest cases in
  [`tests/synthetic/test_compact_restore.py`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/synthetic/test_compact_restore.py).
- ADRs per Lab (e.g. wiki-ingest: 0005, 0006, 0007, 0008;
  wiki-compiler: 0001, 0002, 0008).

### 5.5 Phase D (Technology)

- [`architecture.md`](../../phase-d-technology-architecture/architecture.md);
  ADR 0004 (nvidia-driver), ADR 0005 (inference-subsystem).

### 5.6 Phase E (Opportunities & Solutions)

- [`README.md`](../../phase-e-opportunities-and-solutions/README.md);
  [`roadmap.md`](../../phase-e-opportunities-and-solutions/roadmap.md).
  Today's gaps are enumerated implicitly via R-NN trajectories
  + audit findings; formal Phase-E gap-catalogue process queued.

### 5.7 Phase F (Migration / R&D)

- 5 experiment artifacts:
  [`K1-modules-000-001.md`](../../phase-f-migration-planning/experiments/K1-modules-000-001.md),
  [`K2-compact-restore.md`](../../phase-f-migration-planning/experiments/K2-compact-restore.md),
  [`G1-blackwell-stability.md`](../../phase-f-migration-planning/experiments/G1-blackwell-stability.md),
  [`G2-MoE-faster-inference.md`](../../phase-f-migration-planning/experiments/G2-MoE-faster-inference.md),
  [`G3-gemma-4-31b.md`](../../phase-f-migration-planning/experiments/G3-gemma-4-31b.md).
- ADR 0006 (inference-deploy session).

### 5.8 Phase G (Implementation Governance)

- [`operations.md`](../../phase-g-implementation-governance/operations.md)
  — runbook + `## Operational log` (DevOps append-only;
  1 dated entry today).
- [`lab-AGENTS-template.md`](../../phase-g-implementation-governance/lab-AGENTS-template.md).
- ADR 0007 (labs restructure self-contained caddy).

### 5.9 Phase H (Architecture Change Management)

- [`audit-process.md`](../../phase-h-architecture-change-management/audit-process.md)
  — 22 predicates (P1..P22).
- 22 audit artifacts (`audit-2026-04-25.md` through
  `audit-2026-05-01r.md`) — append-only history of conformance
  walks.
- [`trajectory-model.md`](../../phase-h-architecture-change-management/trajectory-model.md).
- 4 lab `test-AGENTS.md` files (regression-locked Phase A-H
  discipline per Lab).

### 5.10 Phase Requirements Management

- [`catalog.md`](../../phase-requirements-management/catalog.md)
  — 15 active R-NN trajectory rows.
- [`process.md`](../../phase-requirements-management/process.md);
  [`wiki-requirements-collection.md`](../../phase-requirements-management/wiki-requirements-collection.md)
  (S1..S8); [`wiki-customer-interview.md`](../../phase-requirements-management/wiki-customer-interview.md)
  (CI-1..7).

### 5.11 Tests + Runners

- 10 test md artifacts under [`/tests/`](../../tests/) — 7 role
  test md (test-auditor, test-wiki-pm, test-developer,
  test-devops, test-source-author, test-concept-curator,
  test-AGENTS for 4 labs) + smoke + synthetic K2 fixture.
- 7 runners under
  [`/scripts/test-runners/`](../../scripts/test-runners/) +
  `_score_history.py` + `aggregate-scores.py` +
  `measure-corpus-recall.py`.
- 7 JSONL score-history artifacts under
  [`/scripts/test-runners/.score-history/`](../../scripts/test-runners/.score-history/)
  (append-only verdict log per ADR 0015 dec 5).

### 5.12 Wiki content repos (sibling repos, in scope)

- `kurpatov-wiki-raw` — 61 raw.json transcripts under
  `data/<course>/<module>/<stem>/raw.json`.
- `kurpatov-wiki-wiki` — 2 source.md + 51 concept.md +
  concept-index.json.

## 6. Implementation & Migration (ArchiMate §7)

- **Plateau (current)** — commit pending. Capability at
  Level 1 across most quality dimensions:
  - K2 L1 shipped at 2.7% saved-time on real lecture A.
  - K2 L2-original deleted; L3 BUILD-next.
  - 12 audited units across Roles + Lab AGENTS files.
  - Per-persona pain ledgers empty; first CI-1..7 cycle pending.
- **Plateau (target)** — trip-quality ≥ 0.50 per-persona;
  SA-01/SA-02 closed; CC-03/CC-04 closed; 100+ concept.md;
  44+ source.md (K1 modules 000+001 complete).
- **Gap** — formally enumerated in catalog.md R-NN trajectories
  + audit-2026-05-01p..r INFO findings.
- **Work Package** (active) — K2 (compact-restore R&D
  experiment). Past plateaus: K2-R1 (synth, V4 0.2261 PASS),
  K2-R2 (real-A V4 0.0116 FAIL), K2-R3 (real-A V5 0.0243 FAIL),
  K2-Step 0 (probe: L2 STOP, L3 GO). Next: K2-R4 / first
  CI-1..7 cycle.

## 7. Self-measurement (the Capability scores itself)

Per ADR 0015 dec 5 + dec 6, the Capability tracks per-Role
verdict history in JSONL + emits an aggregate table the Auditor
walks under P22 + AU-11.

**Today's verdict totals at commit pending:**

- 7 runners → 70 verdicts (66 PASS, 3 italian-strike, 1 FAIL).
- 30 pytest cases → 30 PASS.
- **Grand total: 100 verdicts; 96 PASS-class; 4 non-PASS** (1
  FAIL = SA-01 missing `language` field, R-NN-backed; 3
  italian-strike = DV-02 backfill-spec, SA-02 missing `## Лекция`,
  CC-03 forward-only links — all R-NN-backed).

**Per-unit aggregate** (12 units in the canonical table per
P22; see audit-2026-05-01r):

| Unit | Score | Band |
|---|---|---|
| Architect | n/a | transitive (audit-process) |
| Auditor | 35/38 = 0.921 | PASS |
| Wiki PM | 33/33 = 1.000 | PASS |
| Developer | 8/9 = 0.889 | PASS |
| DevOps | 10/10 = 1.000 | PASS |
| Source-author | 9/11 = 0.818 | PASS |
| Concept-curator | 6.98/8.0 = 0.873 | PASS |
| Wiki Customer (5 personas) | n/a | transitive (CI-3..5) |
| 4 × lab AGENTS.md | 4/4 = 1.000 each | PASS |

The Capability is at **0.93 mean across 10 scored units** —
PASS band but with measurable per-Role gaps the open R-NN
trajectories are chasing.

## 8. What this Capability is good at

- Falsifier-first measurement (Step 0 probe pattern, K2 lesson).
- TDD discipline with verifiable reward functions (ADR 0015).
- Cheap-experiment principle (P5).
- Single-decision-maker velocity (P1).
- Containerised production (P3).
- Audit-driven governance with verifiable scores (ADR 0015 dec
  5 + dec 6 + audit-process).

## 9. What it's not (yet) good at

- L2 / L3 compaction (queued; L3 probe-validated, L2-original
  falsified).
- Real customer ledgers (cycle is scaffolded but no real run
  yet — first CI-1..7 against lecture A is the next move).
- Multi-host deployment (P4 wall by design; not a gap).
- LLM-as-judge for paraphrase tolerance (L4 conditional).
- Per-persona runner (CU-NN cases) — Wiki Customer aggregate
  remains transitive until shipped.


## Motivation chain

Per [P7](../../phase-preliminary/architecture-principles.md):

- **Driver**: a synthesis artifact unifies the per-phase
  fragments and makes the Capability's realisation grep-able
  end-to-end.
- **Goal**: Architect-velocity (one entry-point to navigate
  the whole stack).
- **Outcome**: AU-11 + P22 walk the synthesis; future Cowork
  sessions load this file as the single anchor.
- **Capability realised**: Architecture knowledge management
  ([forge-level.md](forge-level.md)).
- **Function**: Synthesise-the-Capability-realisation.
- **Element**: this file.
