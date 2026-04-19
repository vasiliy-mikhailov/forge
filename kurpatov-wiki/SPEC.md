# kurpatov-wiki — SPEC

## Purpose
Automatically build a structured "wiki" from Kurpatov's video lectures
("Karpathy-style LLM notes" methodology). Inputs are `.mp4` files from his
courses; outputs are first a transcript, then per-video summaries / notes,
then an assembled wiki.

The problem is solved in layers (see ADR 0001 "two-layer vault"):

```
videos/     → vault/raw/     → vault/wiki/
(.mp4)        (raw.json)       (markdown, not yet assembled)
```

Today the first two steps are implemented: scanning and transcription. The
LLM layer and wiki assembly are in progress.

## Non-goals
- Not multimodal — video content (frames, gestures) is not analyzed.
  Audio only.
- Not publishing. The wiki will end up as markdown + navigation; hosting
  and rendering are out of scope for this service.
- Not real-time. Latency target is "a couple of minutes after the file is
  copied in".
- Not multi-user. Just me.

## Architecture
Two long-running roles inside a single docker-compose project (see
`docker-compose.yml`):

1. **`jupyter-kurpatov-wiki`** — Jupyter for manual experiments and batch
   runs (`02_transcribe_incremental.py`). Torch + faster-whisper +
   pyannote.audio in a venv. Served via caddy + basic auth.

2. **`kurpatov-transcriber`** — headless daemon running
   `03_watch_and_transcribe.py`. It reactively watches `videos/` and
   transcribes new files as soon as they stabilize. Model is lazy-loaded
   on the first task and unloaded after N seconds of idle (see ADR 0003).
   Same image, same network, same GPU.

Both services have access to:

- `${STORAGE_ROOT}/kurpatov-wiki/videos/` → `/workspace/videos/` (mounted
  rw but effectively read-only).
- `${STORAGE_ROOT}/kurpatov-wiki/vault/` → `/workspace/vault/` (rw).
- `${STORAGE_ROOT}/models/` → `/workspace/models/` (shared HF cache with
  rl-2048).

## Data contracts

### Inputs: `videos/`
Arbitrary directory hierarchy. Typical:

```
videos/
└── <course>/
    └── <module>/
        └── <lecture-name>.mp4
```

Any depth of nesting is allowed — both the watcher and the incremental
script mirror the structure (see ADR 0004).

### RAW layer: `vault/raw/<same dirs>/<stem>/raw.json`
Stable contract (see ADR 0002 "JSON-only, single file"):

```json
{
  "info": {
    "language": "ru",
    "duration": 3210.12,
    "language_probability": 0.98,
    "source_path": "/workspace/videos/Psychologist-consultant/.../005 ... .mp4",
    "model": "large-v3",
    "compute_type": "float16",
    "beam_size": 5,
    "transcribed_at": "2026-04-19T08:30:00Z",
    "diarized": false
  },
  "segments": [
    {
      "id": 1,
      "start": 0.0,
      "end": 4.32,
      "text": "...",
      "speaker": null,
      "words": [{"start": 0.0, "end": 0.3, "word": "Hello", "prob": 0.98}, ...]
    },
    ...
  ]
}
```

- `info.source_path` — absolute path inside the container. Needed for:
  migration (`migrate_vault_hierarchy.py`), and for binding wiki pages back
  to videos later.
- `info.diarized` — flag that `segments[].speaker` is populated. Currently
  always `false`; a later pyannote step will set it.
- Atomicity: the file is written to `<stem>.tmp/raw.json`, then the
  directory is renamed to `<stem>/`.

### WIKI layer: `vault/wiki/`
Out of scope for this SPEC today. Expected: markdown files with notes,
linked to raw.json via `info.source_path`.

## Invariants

1. **Transcription is idempotent.** If `raw.json` for a video exists and is
   not corrupt, both scripts (02 and 03) skip it.
2. **Hierarchy is mirrored.**
   `out_dir = vault/raw / video.relative_to(videos).with_suffix("")`. The
   old flat layout is considered incompatible; migrate with
   `migrate_vault_hierarchy.py` (see ADR 0004).
3. **Only one GPU consumer at a time.** Jupyter and the transcriber share
   one GPU (`KURPATOV_WIKI_GPU_UUID`), but the transcriber unloads its
   model while idle so jupyter can use the memory for experiments
   (see ADR 0003).
4. **File stability before processing.** The watcher waits until the mp4's
   size and mtime stop changing for `--stable-sec` seconds (default 10).
   This protects against processing a half-copied file from
   rsync/scp/cp.
5. **Model format is fixed.** `large-v3`, `float16`, `beam=5`,
   `language=ru`, word timestamps, VAD with `min_silence_duration_ms=500`.
   Any deviation requires a SPEC update and most likely a migration — the
   config is recorded in `info` so transcripts of different "generations"
   can be told apart later.

## Status
Production for the RAW layer. Running since April 2026.

Done:
- Two roles in compose (jupyter + transcriber).
- Reactive watcher with lazy-load / idle-unload of the model.
- Full mirror of the videos → vault/raw hierarchy.
- Migration script for the flat layout.

Not yet:
- Diarization (pyannote). Placeholder in the format is there; the HF token
  hasn't been obtained.
- LLM summary per video.
- Wiki assembly.

## Open questions
- How to split long lectures into semantic blocks (by time? by VAD pauses?
  by sentences in the text?).
- Do we need a separate "clean transcript" layer (no timings) to feed into
  the LLM, or is `segments[].text` enough?
- Where to keep prompts for summarization — in code or as standalone
  markdown files in `kurpatov-wiki/prompts/`.
- Determinism and reproducibility for pyannote: how to pin checkpoint
  versions.

## Running
```bash
# Drop videos in:
mkdir -p ${STORAGE_ROOT}/kurpatov-wiki/videos/Psychologist-consultant/05-conflicts
cp ~/downloads/*.mp4 ${STORAGE_ROOT}/kurpatov-wiki/videos/Psychologist-consultant/05-conflicts/

# Bring up (from the forge root):
make kurpatov-wiki

# The watcher picks them up on its own. Batch pass over everything missing:
docker exec -t jupyter-kurpatov-wiki \
  python -u /workspace/notebooks/02_transcribe_incremental.py
```

See also: `docs/adr/0001` through `0004`,
`notebooks/02_transcribe_incremental.py`,
`notebooks/03_watch_and_transcribe.py`,
`notebooks/migrate_vault_hierarchy.py`.
