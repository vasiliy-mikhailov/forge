# ADR 0004 — vault/raw/ fully mirrors the sources/ hierarchy

## Status
Accepted (2026-04-19). Supersedes the original flat layout; transition was
done via a one-off `migrate_vault_hierarchy.py`.

Amended (2026-04-19 — data/ content split). The Decision section
below places the mirrored hierarchy directly under `vault/raw/`.
Post-amendment, it lives one segment deeper, under
`vault/raw/data/<course>/<module>/<stem>/raw.json`, so that meta
files at the repo root (`README.md`, `CLAUDE.md`, CI config) cannot
collide with a top-level course directory in the same namespace.
The hierarchy itself — course / module / stem, stem-as-directory —
is unchanged. See [ADR 0005](0005-split-transcribe-and-push.md)
(data/ content-split amendment) for the migration and the pusher
`--vault` / `--raw` path split that made the move possible without
relocating `.git/`.

Amended (2026-04-20 — videos/ → sources/ rename). The input
directory was renamed from `videos/` to `sources/` once the pipeline
widened its scope to include non-video media (`.mp3`, `.m4a`, ...).
This ADR uses the new name throughout; wherever the text below says
`sources/`, the corresponding pre-rename path was `videos/`. The
mirror invariant (output path = input path with the root swapped
and the suffix stripped) is unchanged. The accepted-suffix
allow-list lives (post-2026-04-20) as `INGEST_EXTENSIONS` =
`WHISPER_EXTENSIONS | HTML_EXTENSIONS` in
`kurpatov-wiki/notebooks/02_ingest_incremental.py` and
`03_watch_and_ingest.py`.

Amended (2026-04-20 — HTML sources keep their extension in the slug).
The mirror rule below (`with_suffix("")` — drop the extension) is
specific to the whisper path. HTML sources (`.html`, `.htm`) keep
their extension in the output directory name:

```
sources/<m>/<stem>.mp4   → raw/data/<m>/<stem>/raw.json       (whisper)
sources/<m>/<stem>.html  → raw/data/<m>/<stem>.html/raw.json  (html)
```

This keeps a media file and an HTML page sharing the same stem
from overwriting each other in the raw tree. The dispatch logic
and rename rationale live in
[ADR 0008](0008-ingest-dispatch.md); the code lives in
`out_slug_for(...)` inside `02_ingest_incremental.py` and
`03_watch_and_ingest.py`.

## Context
Originally the transcription script stored `raw.json` in a **flat**
layout:

```
sources/Psychologist-consultant/05-conflicts/005 Conflict nature.mp4
→ vault/raw/005 Conflict nature/raw.json
```

Problems:

- The course/module info is lost.
- Future modules will have `001 ...`, `002 ...`, `003 ...` with similar
  naming across modules — name collisions are inevitable.
- Wiki assembly expects to know "which module a lecture belongs to" —
  otherwise there's no natural navigation.

## Decision
`vault/raw/` **fully mirrors** the `sources/` hierarchy. The output path:

```python
out_dir = vault_raw_root / source.relative_to(sources_root).with_suffix("")
```

For the example above:

```
sources/Psychologist-consultant/05-conflicts/005 Conflict nature.mp4
→ vault/raw/Psychologist-consultant/05-conflicts/005 Conflict nature/raw.json
```

The last component (stripped of extension) stays a directory, so it can
eventually hold siblings (`words.srt`, `diarized.json` — see ADR 0002 on
format; today only one file lives there, but the slot exists).

## Consequences
- Plus: wiki navigation follows trivially from the hierarchy.
- Plus: no collisions by `stem`.
- Plus: copying one module to another machine is a simple `rsync` of a
  subdirectory.
- Minus: path depth grows. Not a problem on ext4/ZFS, theoretically an
  issue on a Windows share.

## Migration
`migrate_vault_hierarchy.py`:

- Reads the legacy `vault/raw/<stem>/raw.json`.
- Uses `info.source_path` to compute the correct destination.
- `shutil.move`s the old directory into place.
- Idempotent: if a file is already in the right place, it's skipped.
- Must run inside the container as root (the raw files are root-owned
  because the container wrote them).

One-off script; keep it — useful as a template if we migrate again.

## Alternatives considered
- **Flat layout + a side `meta.json` with the course path.** More complex,
  same result.
- **Lecture identifier (uuid/hash of `source_path`) as the folder name.**
  Clean, but painful for me to eyeball.
