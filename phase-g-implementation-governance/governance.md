# Implementation governance

The *operational* rules — what to do and not do day-to-day in the
working tree. The meta-decisions about how forge does architecture
at all (architecture team, framework choice, principles, method,
repository layout) live one layer above in
[`../phase-preliminary/`](../phase-preliminary/) and are not
re-stated here.

## Forge-wide rules

- **All work runs in containers.** Source of truth:
  [`policies/containers.md`](policies/containers.md). This is the
  enforcement of the
  [`P3 — containers-only`](../phase-preliminary/architecture-principles.md)
  principle.
- **AGENTS.md per location** is canonical at every directory.
  CLAUDE.md is a symlink → AGENTS.md at every location. Convention
  established in
  [`../phase-preliminary/architecture-repository.md`](../phase-preliminary/architecture-repository.md).
- **Single source of truth per location.** If AGENTS.md (or
  AGENTS.md plus its phase-folder pages) conflicts with code, fix
  one or the other but do not let drift persist.
- **SPEC.md is source of truth for code.** If code diverges from
  SPEC, don't silently change code — either update SPEC or
  reconcile code to spec.
- **Idempotency.** Any change to a Dockerfile, compose file, or
  Makefile must survive a rebuild and restart. No manual "ssh in
  and do X" steps.
- **One change per edit.** Don't mix refactors with new features.
- **Secrets only in `.env`.** No tokens, passwords, certificates
  in git. If you see something that looks like a secret, stop and
  ask.
- **Data lives under `${STORAGE_ROOT}`**, not in the forge repo.
  `vault/`, `sources/`, `models/`, `checkpoints/`, `mlruns/` are
  never committed to forge. Note: `vault/raw/` (under
  `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/`) **is** a git
  working tree — but for a *separate* repo
  (`kurpatov-wiki-raw`), pushed by the
  `kurpatov-wiki-raw-pusher` container. See
  [`../phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md`](../phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md).
- **ADR for irreversible decisions.** If on-disk data format
  changes, the framework choice changes, or the network topology
  changes — add
  `phase-<x>/adr/NNNN-*.md` or
  `phase-c-…/application-architecture/<lab>/{docs/adr,adr}/NNNN-*.md`
  (lab-scoped) where NNNN is the next free number.

## Forge-wide don't

- Don't run multiple writers against the mlflow SQLite at the
  same time.
- Labs are mutex on host ports 80/443 (each lab's caddy binds
  them). `wiki-compiler` + `wiki-bench` is the one permitted
  co-running combination (bench is a client without a caddy).
  All other lab combinations: stop one, start another via
  `make <a>-down && make <b>`.
- Don't give two labs overlapping GPU UUIDs in `.env`. The
  Blackwell hosts compiler OR rl-2048 (not both); the RTX 5090
  hosts wiki-ingest. Going to dual-GPU TP for compiler takes both
  cards — wiki-ingest must be down then.
- Don't commit `.ipynb` files or large `.pt` / `.bin` blobs.
- Don't change the
  `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/data/<path>/raw.json`
  format without an ADR — the watcher and every downstream layer
  depend on it.
- Don't reinstall the proprietary nvidia driver (without
  `-open`) and don't delete `/etc/modprobe.d/nvidia-uvm.conf`.
  Multi-GPU on Blackwell does not forgive this. Details and
  symptoms →
  [`../phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md`](../phase-d-technology-architecture/adr/0004-nvidia-driver-open-plus-hmm-off.md);
  diagnostics → [`operations.md`](operations.md) §
  "GPU suddenly unavailable".

## Per-lab AGENTS.md must follow the canonical template

Every lab's `AGENTS.md` follows the canonical Phase A-H template
in [`lab-AGENTS-template.md`](lab-AGENTS-template.md). The
template itself is a Preliminary-phase artefact (it defines how
labs participate in the architecture); maintenance of the
template lives here under Phase G.

Labs that don't yet have AGENTS.md must add one when their next
substantive change lands. Until then, the forge-level AGENTS.md
is the authoritative reference for those labs.

## Lab-local governance

Lab-specific do / don't lists live in each lab's AGENTS.md
Phase G section, not here. Examples:

- "GPU 0 hosts compiler OR rl-2048 not both" — lives in
  `wiki-compiler/AGENTS.md` § Phase G.
- "Always `docker stop --time 10` before `docker rm -f` for
  CUDA-active containers" — lives in `wiki-compiler/AGENTS.md`
  § Phase G.
- "Bench artefacts go to `${STORAGE_ROOT}/labs/wiki-bench/...`"
  — lives in `wiki-bench/AGENTS.md` § Phase G.

## Cross-references

- [`policies/`](policies/) — forge-wide policy documents
  (today: containers).
- [`operations.md`](operations.md) — runbook material for the
  architect (quick start, GPU recovery, smoke-test contract,
  backup priorities).
- [`lab-AGENTS-template.md`](lab-AGENTS-template.md) — the
  canonical per-lab Phase A-H template.
- [`adr/`](adr/) — Phase G scoped ADRs (governance / process
  decisions).
- [`../phase-preliminary/`](../phase-preliminary/) — the
  meta-decisions this phase enforces.
