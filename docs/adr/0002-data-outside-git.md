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
- **In git**: (1). Code and configs, plus SPEC and ADR files, plus
  `.env.example` as a template.
- **Outside git, in a password manager**: (2). Secrets. `.gitignore`
  explicitly excludes `.env`.
- **Outside git, under `${STORAGE_ROOT}` with its own backup strategy**:
  (3). Data. `.gitignore` excludes `vault/`, `models/`, `videos/`,
  `checkpoints/`, `mlruns/`, `mlflow/data/`.

## Consequences
- Plus: the repo stays small; commits are essentially text.
- Plus: no CRLF/LFS/pre-commit hell.
- Plus: forced separation — it's obvious what to back up as code vs. as
  data.
- Minus: disaster recovery needs two sources: git and a separate data
  backup. See `docs/operations.md` → "Disaster recovery".
- Minus: when onboarding a new agent/tool I have to separately explain
  where data actually lives.

## Follow-ups
- `.env.example` must contain every variable referenced in compose,
  Caddyfile, or Dockerfile.
- If CI ever appears, it will not have access to `.env`, and tests must
  either work without secrets or use `.env.ci`.
