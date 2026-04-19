# kurpatov-wiki — SPEC

## Purpose
Automatically build a structured "wiki" from Kurpatov's video lectures
("Karpathy-style LLM notes" methodology). Inputs are `.mp4` files from his
courses; outputs are first a transcript, then per-video summaries / notes,
then an assembled wiki.

The problem is solved in layers (see ADR 0001 "two-layer vault"):

```
videos/     → vault/raw/data/  → kurpatov-wiki-wiki/data/
(.mp4)        (raw.json)          (markdown, Mac-authored)
```

Both published repos use a `data/` subtree so meta files
(`CLAUDE.md`, `README.md`, etc.) don't share a namespace with
course slugs. See ADR 0005's data/content-split amendment (raw
side) and ADR 0007's amendment (wiki side).

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
Three long-running roles inside a single docker-compose project (see
`docker-compose.yml`), each with a single responsibility. They share
state only through the vault filesystem — no code, no network RPC.

1. **`jupyter-kurpatov-wiki`** — Jupyter for manual experiments and batch
   runs (`02_transcribe_incremental.py`). Torch + faster-whisper +
   pyannote.audio in a venv. Served via caddy + basic auth. Uses
   `KURPATOV_WIKI_GPU_UUID`. Image: `forge-kurpatov-wiki:latest`
   (CUDA base, ~20 GB).

2. **`kurpatov-transcriber`** — headless daemon running
   `03_watch_and_transcribe.py`. Reactively watches `videos/` and
   transcribes new files as soon as they stabilize. Model is lazy-loaded
   on the first task and unloaded after N seconds of idle (see ADR 0003).
   Same image, same network, same GPU as jupyter. Knows nothing about
   git.

3. **`kurpatov-wiki-raw-pusher`** — headless daemon running
   `04_watch_raw_and_push.py`. Reactively watches `vault/raw/data/`
   (content subtree) and commits from the `vault/raw/` git working
   tree, pushing new transcripts to the private `kurpatov-wiki-raw`
   GitHub repo (see ADR 0005). No GPU, no network exposure other
   than outbound SSH to GitHub. Knows nothing about whisper or
   videos. Runs a dedicated lean image
   `forge-kurpatov-wiki-pusher:latest` (`python:3.12-slim` + git +
   openssh-client + watchdog, ~200 MB) — see ADR 0006. Built from
   `kurpatov-wiki/Dockerfile.pusher`.

Volume access by service:

| Mount inside container            | jupyter | transcriber | raw-pusher |
| --------------------------------- | :-----: | :---------: | :--------: |
| `/workspace/videos/` (ro-ish)     |   rw    |     rw      |     —      |
| `/workspace/vault/`               |   rw    |     rw      |     rw     |
| `/workspace/models/` (HF cache)   |   rw    |     rw      |     —      |
| `/workspace/checkpoints/`         |   rw    |     rw      |     —      |
| `/root/.ssh/kurpatov-wiki-vault`  |   —     |      —      |     ro     |

Host paths:

- `${STORAGE_ROOT}/kurpatov-wiki/videos/` — input .mp4 tree.
- `${STORAGE_ROOT}/kurpatov-wiki/vault/` — vault root. Contains
  `raw/` (a git working tree for the `kurpatov-wiki-raw` repo; its
  content lives under `raw/data/<course>/<module>/<stem>/`). The
  parallel `wiki/` layer is not created here — the wiki is authored
  and pushed from the operator's Mac (ADR 0007).
- `${STORAGE_ROOT}/models/` — shared HF cache with rl-2048.
- `~/.ssh/kurpatov-wiki-vault` — per-repo deploy key for the raw repo;
  filename keeps the legacy "vault" name for now (see ADR 0005 →
  Follow-ups).

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

### RAW layer: `vault/raw/data/<same dirs>/<stem>/raw.json`
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

### WIKI layer: `kurpatov-wiki-wiki` (GitHub-canonical, Mac-authored)

Unlike the RAW layer, the wiki layer is **not** written from the server.
Full decision record: [ADR 0007](docs/adr/0007-wiki-layer-mac-side.md).
Authoring happens in a Claude Desktop (Cowork) session on the operator's
Mac, which reads the `kurpatov-wiki-raw` repo and writes the
`kurpatov-wiki-wiki` repo directly. `${STORAGE_ROOT}/kurpatov-wiki/vault/
wiki/` is **not** created by `make setup` and has no server-side
consumer; the canonical wiki lives on GitHub.

Repo layout (meta at the root, content under `data/`):

```
kurpatov-wiki-wiki/               (repo root)
├── CLAUDE.md                     session entrypoint
├── README.md                     reading protocol + conventions
├── prompts/                      authoring prompts
├── docs/                         design.md + authoring.md
└── data/                         all content lives here
    ├── index.md                  course/module/video order + A-Z concept index
    ├── concept-index.json        authoritative authoring state (see below)
    ├── concepts/
    │   ├── _template.md
    │   ├── <concept-slug>.md     one per psychological concept
    │   └── ...
    └── videos/
        ├── _template.md
        └── <course>/<module>/<stem>.md   one per source video
```

Two article types (see ADR 0007):

- **Video article** — three required sections:
  `## TL;DR` (1-2 sentences), `## New ideas` (ideas first introduced
  in this video, not in any previously-processed video — the
  fast-reader's path), `## All ideas` (full ideational content
  grouped by concept, with cross-links to `concepts/`).
  Frontmatter carries `slug`, `course`, `module`, `source_raw`,
  `processed_at`, `concepts_touched`, `concepts_introduced`. There
  is no numeric `order:` field — module names are zero-padded
  (`05-conflicts`) and stems carry zero-padded numeric prefixes
  (`005 Conflict nature`), so sorted-path order equals course
  order (see ADR 0007 invariants).

- **Concept article** — an append-only article per psychological
  concept. A short top-of-article definition, followed by a
  "Contributions by video" log where each entry names a video slug
  and summarizes what that video adds to the concept. Never
  rewritten destructively; fixes are explicit edits with reasons.

`data/concept-index.json` is the authoring state file (ADR 0007 →
Invariants). Every Mac-side session reads it at start, uses it to
decide what's "new" in the next video, and commits the updated
version at the end. Drift between this file and the `data/concepts/`
directory is a bug; the wiki-repo playbook at
`kurpatov-wiki-wiki/docs/authoring.md` spells out how to detect
and repair it. The forge-side mirror lives at
[docs/mac-side-wiki-authoring.md](docs/mac-side-wiki-authoring.md).

### Published repos

| GitHub repo             | Pushed by                               | Working tree                                         |
| ----------------------- | --------------------------------------- | ---------------------------------------------------- |
| `kurpatov-wiki-raw`     | `kurpatov-wiki-raw-pusher` (container)  | server: `${STORAGE_ROOT}/kurpatov-wiki/vault/raw/`   |
| `kurpatov-wiki-wiki`    | Claude Desktop / Cowork session         | Mac: `~/forge-wikiwork/wiki/` (by convention)        |

In the `kurpatov-wiki-raw` repo, raw transcripts live under a
`data/` subtree: `data/<course>/<module>/<stem>/raw.json`. The repo
root is reserved for future meta files. On the server the git
working tree sits at `${STORAGE_ROOT}/kurpatov-wiki/vault/raw/` and
the pusher's `--raw` (watch subtree) points at
`${STORAGE_ROOT}/kurpatov-wiki/vault/raw/data/`. See ADR 0005.

In the `kurpatov-wiki-wiki` repo, content lives under `data/`
(articles, concept-index, nav); meta (CLAUDE.md, README, prompts/,
docs/) lives at the root. See ADR 0007.

## Invariants

1. **Transcription is idempotent.** If `raw.json` for a video exists and is
   not corrupt, both scripts (02 and 03) skip it.
2. **Hierarchy is mirrored under `data/`.**
   `out_dir = vault/raw/data / video.relative_to(videos).with_suffix("")`.
   The old flat layout is considered incompatible; migrate with
   `migrate_vault_hierarchy.py` (see ADR 0004). The `data/` prefix
   is per ADR 0005's data/content-split amendment.
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
- Three roles in compose (jupyter + transcriber + raw-pusher).
- Reactive watcher with lazy-load / idle-unload of the model.
- Full mirror of the videos → vault/raw/data hierarchy.
- Migration script for the flat layout (ADR 0004); subsequent
  data/-subtree migration via the server-side script documented in
  ADR 0005's amendment.
- Continuous auto-push of `vault/raw/data/` to the
  `kurpatov-wiki-raw` private GitHub repo, with debounced commits
  (see ADR 0005).

Not yet:
- Diarization (pyannote). Placeholder in the format is there; the HF token
  hasn't been obtained.
- LLM summary per video (design: ADR 0007; content: Mac-side Claude
  Desktop sessions, pending operator time).
- Concept articles populated beyond scaffolding.

## Open questions
- How to split long lectures into semantic blocks for the "All ideas"
  section (by time? by VAD pauses? by thematic shift? Currently left to
  the Mac-side session's judgment — see the playbook).
- Concept vocabulary drift across English and Russian. Concept slugs are
  English kebab-case; article prose follows whichever language reads best
  for the concept. Playbook captures the resolution rule.
- Determinism and reproducibility for pyannote: how to pin checkpoint
  versions.
- When (if ever) the wiki layer needs automation. Today's cadence matches
  Mac-side sessions; if volume grows, revisit per ADR 0007 follow-ups.

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

See also: `docs/adr/0001` through `0007`,
`docs/mac-side-wiki-authoring.md` (wiki-layer playbook),
`prompts/per-video-summarize.md`, `prompts/concept-article.md`,
`notebooks/02_transcribe_incremental.py`,
`notebooks/03_watch_and_transcribe.py`,
`notebooks/04_watch_raw_and_push.py`,
`notebooks/migrate_vault_hierarchy.py`.
