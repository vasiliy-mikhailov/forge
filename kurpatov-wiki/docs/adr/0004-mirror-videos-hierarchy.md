# ADR 0004 — vault/raw/ fully mirrors the videos/ hierarchy

## Status
Accepted (2026-04-19). Supersedes the original flat layout; transition was
done via a one-off `migrate_vault_hierarchy.py`.

## Context
Originally the transcription script stored `raw.json` in a **flat**
layout:

```
videos/Psychologist-consultant/05-conflicts/005 Conflict nature.mp4
→ vault/raw/005 Conflict nature/raw.json
```

Problems:

- The course/module info is lost.
- Future modules will have `001 ...`, `002 ...`, `003 ...` with similar
  naming across modules — name collisions are inevitable.
- Wiki assembly expects to know "which module a lecture belongs to" —
  otherwise there's no natural navigation.

## Decision
`vault/raw/` **fully mirrors** the `videos/` hierarchy. The output path:

```python
out_dir = vault_raw_root / video.relative_to(videos_root).with_suffix("")
```

For the example above:

```
videos/Psychologist-consultant/05-conflicts/005 Conflict nature.mp4
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
