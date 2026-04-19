# ADR 0002 — RAW layer: one JSON file per video

## Status
Accepted (2026-04-19).

Amended (2026-04-19 — data/ content split). The path shown in the
Decision section below (`vault/raw/<path>/<stem>/raw.json`) is now
off by one `data/` segment: the transcriber writes to
`vault/raw/data/<path>/<stem>/raw.json`, and the pusher watches
`vault/raw/data/` while keeping its git working tree at
`vault/raw/` so the existing `.git/` keeps working without being
moved. File format (one JSON per video) is unchanged — only the
parent directory grew a `data/` prefix. Rationale and migration
are in [ADR 0005](0005-split-transcribe-and-push.md) (data/
content-split amendment).

## Context
faster-whisper emits segments (with timings and optionally words with
probabilities) plus an `info` object with language/duration/model
metadata. Possible storage formats:

1. Multiple files per video: `transcript.json`, `segments.csv`,
   `words.parquet`, `meta.yaml`.
2. One JSON file per video containing everything.
3. A shared DB (SQLite/Postgres) with a `segments` table and a `meta` table.

Criteria:

- Cheap atomic writes (a video may run for hours; we don't want to leave
  partial state after an interrupt).
- Easy to eyeball (I `cat` these files a lot).
- Easy to `grep` for text search.
- Easy to migrate to a DB later without rewriting transcription.

## Decision
One file per video at `vault/raw/<path>/<stem>/raw.json`. Shape:

- `info` — a dict of metadata;
- `segments[]` — an array, each entry a segment with `start`, `end`,
  `text`, `speaker`, `words[]`.

Atomic write via `<stem>.tmp/raw.json` → `rename(<stem>.tmp → <stem>)`.

## Consequences
- Plus: one file = one unit. Delete it → it will be regenerated on the
  next run.
- Plus: no global state, transcription can be parallelized across machines
  trivially — merge is `cp`.
- Plus: JSON is greppable and parseable. Loading everything into SQLite
  later is 10 lines of code.
- Minus: with tens of thousands of segments the JSON gets heavy (1+ MB).
  Fine for now.
- Minus: no schema / validation. Compensated by SPEC.md describing the
  format.

## Alternatives considered
- **Multiple files per video.** Complicates atomicity (either a
  transaction or a "done" marker file is required). No upside for today's
  volume.
- **Database.** Adds another component with its own backup story. Defer
  until volume/queries justify it. Migration will be straightforward —
  bulk-load every raw.json into the DB.
