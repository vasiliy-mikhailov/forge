# K2-R2 — Activation playbook (Developer + DevOps)

The K2-R1 (synth) result landed at trip-quality **0.2261**
(V4_aggressive winner) — see
[`/phase-f-migration-planning/experiments/K2-compact-restore.md`](../../../../../phase-f-migration-planning/experiments/K2-compact-restore.md)
Execution log. K2-R2 is the same algorithm against the **real**
lecture A from `kurpatov-wiki-raw` on the
[mikhailov.tech / Blackwell host](../../../../../phase-d-technology-architecture/architecture.md).

This file is the activation kit. A Cowork session loaded with
the [Developer role](../../../../../phase-b-business-architecture/roles/developer.md)
runs steps 1-3; a session loaded with the
[DevOps role](../../../../../phase-b-business-architecture/roles/devops.md)
runs step 4. **No architect time required.**

---

## Step 1 — Developer: locate lecture A on the host

SSH to mikhailov.tech (use the `kurpatov-wiki-vault` deploy key
per [ADR 0005](../../docs/adr/0005-split-transcribe-and-push.md)
naming convention; ControlMaster per
[ADR 0009](../../../../../phase-preliminary/adr/0009-ssh-controlmaster-for-architect-edit-loop.md)):

```bash
ssh mikhailov.tech
# Lecture A's raw.json is published by the wiki-ingest pusher
# (ADR 0005) under the vault path:
RAW=$STORAGE_ROOT/labs/wiki-ingest/vault/raw/data/Психолог-консультант/'000 Путеводитель по программе/000 Знакомство с программой «Психолог-консультант»'/raw.json
ls -la "$RAW"
# expect: ~9963-word transcript per corpus-observations row A
```

If the path differs (the vault layout may have been migrated —
see [migrate_vault_hierarchy.py](../../notebooks/migrate_vault_hierarchy.py)),
locate the file via:

```bash
find "$STORAGE_ROOT/labs/wiki-ingest/vault/raw/data" \
    -name 'raw.json' -path '*000 Знакомство*' -print
```

## Step 2 — DevOps: build the K2 sweep container (one-time)

Per [architecture-principles.md P3](../../../../../phase-preliminary/architecture-principles.md)
(containers-only execution): NO host-Python on `mikhailov.tech`.
The sweep runs inside a docker container that bind-mounts the
forge tree (read-only) and the kurpatov-wiki-raw vault
(read-only).

```bash
cd ~/forge
git pull origin main
docker compose -f phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/compose.k2-sweep.yml \
    build k2-sweep
```

The image is `forge-k2-sweep:latest` — slim Python 3.12 + the
sweep entry point. No GPU. No network. ~150 MB.

## Step 3 — Developer: run the sweep through the container

```bash
docker compose -f phase-c-information-systems-architecture/application-architecture/wiki-bench/compact_restore/compose.k2-sweep.yml \
    run --rm k2-sweep \
    --input "/raw/data/Психолог-консультант/000 Путеводитель по программе/000 Знакомство с программой «Психолог-консультант»/raw.json" \
    --observations /forge/phase-b-business-architecture/products/kurpatov-wiki/corpus-observations.md \
    --source A \
    --run-id K2-R2-real-A \
    --ops-log-stub
```

Inside the container: forge tree at `/forge` (read-only), vault
at `/raw` (read-only). Output goes to stdout; the container has
no writable mounts beyond `/tmp` (64 MB tmpfs).

(Bare-metal `python3 sweep.py` is the *dev* invocation only —
runs on the architect's local Cowork sandbox where Docker isn't
required. On `mikhailov.tech` the container path is mandatory
per P3.)

Expected output (markdown table written to stdout):

- Per-variant ratio + forward recall + trip-quality table.
- Winner variant name.
- L1 hypothesis gate verdict (PASS if trip-quality ≥ 0.20).
- Operations-log stub for DevOps to paste.

The 4 variants execute in seconds (pure-Python regex against ~10K
words; no GPU). The recall harness runs against the 20 source-A
observations in the production corpus-observations file (4
Substance + 7 Form + 9 Air).

## Step 3 — Developer: log the run + paste the table into K2 spec

After the sweep prints, capture both blocks and:

1. Append a new row to the K2 Execution log table in
   [`/phase-f-migration-planning/experiments/K2-compact-restore.md`](../../../../../phase-f-migration-planning/experiments/K2-compact-restore.md)
   under `## Execution log`. Use the per-variant numbers from
   the sweep output. Run_id format: `K2-R2-real-A-<variant>` so
   the row is unique.

2. Optional: log scores to history (only if the sweep changed
   the algorithm — for K2-R2 against an unchanged algorithm, the
   sweep is a *measurement* not a *commit-worthy* run, so this
   step is usually skipped):

   ```bash
   python3 scripts/test-runners/test-developer-runner.py --log-scores
   ```

3. Commit the K2 Execution log update:

   ```bash
   git add phase-f-migration-planning/experiments/K2-compact-restore.md
   git -c user.name=vasiliy-mikhailov \
       -c user.email=vasiliy.mikhailov@gmail.com \
       commit -m "K2-R2 lands: trip-quality <NNNN> on real lecture A from kurpatov-wiki-raw

   Real-corpus result: <variant> wins at trip-quality <0.NNNN>
   (fwd recall <0.NNN>, ratio <0.NNN>) on the 20 source-A
   observations in corpus-observations.md.

   Closes K2 Day 3 sequenced-work entry. Next: K2-R3 (L1+L2+L3)
   when wiki-bench harness implements the L2 / L3 layers.

   serves: K2"
   git push origin main
   ```

## Step 4 — DevOps: append to the operational log

Take the `### Operations log stub` block the sweep emitted and
prepend it to the
[`## Operational log`](../../../../../phase-g-implementation-governance/operations.md)
section in `phase-g-implementation-governance/operations.md`
(newest entry above oldest, per the section's documented format).

Commit:

```bash
git add phase-g-implementation-governance/operations.md
git -c user.name=vasiliy-mikhailov \
    -c user.email=vasiliy.mikhailov@gmail.com \
    commit -m "ops: K2-R2 sweep run logged

Per DevOps role's discipline (DO-02: dated entries; DO-03:
ADR / R-NN cited) the K2-R2 run is logged in operations.md
## Operational log.

serves: K2"
git push origin main
```

## What success looks like

- The K2 Execution log gains a `K2-R2-real-A-<variant>` row per
  variant; the winner row has `gate: PASS` if trip-quality ≥
  0.20 OR a documented falsification note if not.
- `phase-g-…/operations.md` `## Operational log` gains a dated
  entry citing the K2 experiment id and the
  R-B-compact-restore catalog row.
- DV-01..06 and DO-01..06 keep PASSing on the next runner walk
  (commit cites K2; TDD discipline preserved; operational log
  updated).
- Per-unit aggregates in the next audit table reflect any
  Developer / DevOps score changes.

## What "K2-R2 didn't pass the gate" looks like

If trip-quality < 0.20 on real lecture A, the algorithm is
under-specified for the real corpus density. Falsifier outcome:
the K2 hypothesis gate fired honestly. Next steps recorded in
the K2 Post-Mortem section:

- V5 with sentence-start filler patterns (queued in K2-R1
  Insight 1).
- Add `pattern_signature` field to Air observations (queued in
  K2-R1 Insight 2) so air_leakage stops false-positiving on
  surrounding content.
- Or move forward with L2 (cross-source dedup) — L1 alone may
  not be enough; the spec's L1+L2 target is 0.40, which the
  L2 layer should reach even if L1 plateaus.

## What this playbook does NOT need

- Architect time (the playbook is mechanical).
- GPU (the L1 algorithm is pure regex; runs on CPU in seconds).
- LLM calls (no inference; no API costs).
- New ADRs (everything cited already exists).

## Locally-tested before SSH

This sweep tool was end-to-end tested against the synth fixture
from this commit's Cowork session (the same code path runs on
mikhailov.tech). Local sanity-check:

```bash
python3 phase-c-…/wiki-bench/compact_restore/sweep.py --ops-log-stub
# → V4_aggressive trip-quality 0.2261 PASS
```

Differences expected on real lecture A:

- **Higher word count**: real-A is ~9963 words (43× synth).
- **Different filler density**: real Курпатов may have more / fewer
  filler patterns per minute than the hand-crafted synth.
- **Real Substance verbatims**: the 4 source-A Substance
  observations in the production corpus-observations are
  Selye-attribution / лимбическая система / базовые потребности /
  генетическая программа — same shape as the synth tested
  against, so the keyword-extractor should behave consistently.
