# ADR 0002 — data and secrets live outside git

## Status
Accepted (2026-04-19).

## Context
forge has three categories of stuff coexisting:

1. Code and configs (Dockerfiles, compose, Makefiles, scripts, SPECs).
2. Secrets: `.env`, basic-auth hash, `MLFLOW_TRACKING_PASSWORD`.
3. Data: HuggingFace models, video files of lectures, transcripts, mlflow
   artifacts, training checkpoints. Gigabytes to tens of gigabytes.

Question: what gets committed to git.

## Decision
- **In the forge repo (git)**: (1). Code and configs, plus SPEC and ADR
  files, plus `.env.example` as a template.
- **Outside git, in a password manager**: (2). Secrets. `.gitignore`
  explicitly excludes `.env`.
- **Outside the forge repo, under `${STORAGE_ROOT}` with its own backup
  strategy**: (3). Data. `.gitignore` excludes `vault/`, `models/`,
  `sources/`, `checkpoints/`, `mlruns/`, `mlflow/data/` (`sources/`
  was `videos/` prior to the 2026-04-20 rename — see
  [kurpatov-wiki ADR 0004](../application-architecture/wiki-ingest/docs/adr/0004-mirror-sources-hierarchy.md)).

### Exception: `kurpatov-wiki/vault/raw/` is its own repo
The raw-transcripts tree is tracked, but in a *separate* private
GitHub repo (`kurpatov-wiki-raw`), not in forge. On the server,
`${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/` is a git working tree for
that repo, pushed by the `kurpatov-wiki-raw-pusher` container. See
[phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md](../application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md).
The invariant "forge stays code-and-configs only" still holds — this
exception concerns a different repo entirely. A symmetric
`kurpatov-wiki-wiki` repo is planned for the `vault/wiki/` tree.

## Consequences
- Plus: the repo stays small; commits are essentially text.
- Plus: no CRLF/LFS/pre-commit hell.
- Plus: forced separation — it's obvious what to back up as code vs. as
  data.
- Minus: disaster recovery needs two sources: git and a separate data
  backup. See `phase-g-implementation-governance/operations.md` → "Disaster recovery".
- Minus: when onboarding a new agent/tool I have to separately explain
  where data actually lives.

## Follow-ups
- `.env.example` must contain every variable referenced in compose,
  Caddyfile, or Dockerfile.
- If CI ever appears, it will not have access to `.env`, and tests must
  either work without secrets or use `.env.ci`.


## Motivation

Per [P7](../../phase-preliminary/architecture-principles.md) — backfit:

- **Driver**: raw.json files are large + machine-generated;
  storing them in forge proper would inflate the repo.
- **Goal**: Architect-velocity (forge stays small + fast).
- **Outcome**: raw.json lives in `kurpatov-wiki-raw` sibling
  repo per ADR 0002 + ADR 0005; forge references but doesn't
  hold the data.
- **Measurement source**: quality-ledger: pre_prod_share (per ADR 0021)
