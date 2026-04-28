# kurpatov-wiki — SPEC

## Purpose
Automatically build a structured "wiki" from Kurpatov's lectures
("Karpathy-style LLM notes" methodology). Inputs are source media files
(video or audio — typically `.mp4`, but also `.mp3` and friends) from his
courses; outputs are first a transcript, then per-source summaries / notes,
then an assembled wiki.

The problem is solved in layers (see ADR 0001 "two-layer vault"):

```
sources/    → vault/raw/data/  → kurpatov-wiki-wiki/data/
(.mp4,        (raw.json)          (markdown, Mac-authored)
 .mp3, …)
```

by a dedicated extractor (`notebooks/_extract_html.py`) and PDF by
`notebooks/_extract_pdf.py` (text-layer fast path, Qwen2.5-VL-7B
OCR fallback) — both reuse the same raw.json envelope. See ADR
0008 (dispatch) and ADR 0009 (PDF).

Both published repos use a `data/` subtree so meta files
(`CLAUDE.md`, `README.md`, etc.) don't share a namespace with
course slugs. See ADR 0005's data/content-split amendment (raw
side) and ADR 0007's amendment (wiki side).

Today the first two steps are implemented: scanning and ingest
(faster-whisper for media, HTML extractor for getcourse.ru pages,
PDF extractor with OCR fallback; see ADR 0008 + 0009). The LLM
layer and wiki assembly are in progress.

## Non-goals
- Not multimodal — for video inputs only the audio track is used; frames
  and gestures are not analyzed. Audio-only inputs pass through the same
  whisper path. HTML inputs are handled by an HTML-text extractor
  (lecturer prose only; student answers and comments explicitly dropped
  — see ADR 0008) — not the whisper path. PDF inputs use a text-layer
  extractor when the PDF has an embedded text layer, and fall back to
  Qwen2.5-VL-7B page-level OCR when the PDF is an image-only scan (see
  ADR 0009).
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
   runs (`02_ingest_incremental.py`). Torch + faster-whisper +
   pyannote.audio + bs4 in a venv. Served via caddy + basic auth. Uses
   `KURPATOV_WIKI_GPU_UUID`. Image: `forge-kurpatov-wiki:latest`
   (CUDA base, ~20 GB).

2. **`kurpatov-ingest`** — headless daemon running
   `03_watch_and_ingest.py`. Reactively watches `sources/` and ingests
   new source files (any suffix in INGEST_EXTENSIONS) as soon as
   they stabilize. Dispatches by suffix: audio/video → faster-whisper
   (GPU, lazy-load / idle-unload per ADR 0003); HTML →
   `_extract_html.py` (CPU, no model load); PDF → `_extract_pdf.py`
   (text-layer fast path is CPU; the OCR fallback loads Qwen2.5-VL-7B
   on the same GPU, lazy-load / idle-unload — ADR 0009). On every
   startup the daemon also does a reverse scan: any `raw.json` whose
   source no longer exists is reclaimed (two-way sync), and any
   `*.tmp` staging leftover from an interrupted extraction is swept
   (ADR 0008 amendments). Same image, same network, same GPU budget
   as jupyter. Knows nothing about git. See ADR 0008 for the
   dispatch design and the rename from `kurpatov-transcriber`.

3. **`kurpatov-wiki-raw-pusher`** — headless daemon running
   `04_watch_raw_and_push.py`. Reactively watches `vault/raw/data/`
   (content subtree) and commits from the `vault/raw/` git working
   tree, pushing new transcripts to the private `kurpatov-wiki-raw`
   GitHub repo (see ADR 0005). No GPU, no network exposure other
   than outbound SSH to GitHub. Knows nothing about whisper or
   source media. Runs a dedicated lean image
   `forge-kurpatov-wiki-pusher:latest` (`python:3.12-slim` + git +
   openssh-client + watchdog, ~200 MB) — see ADR 0006. Built from
   `kurpatov-wiki/Dockerfile.pusher`.

Volume access by service:

| Mount inside container            | jupyter |   ingest    | raw-pusher |
| --------------------------------- | :-----: | :---------: | :--------: |
| `/workspace/sources/` (ro-ish)    |   rw    |     rw      |     —      |
| `/workspace/vault/`               |   rw    |     rw      |     rw     |
| `/workspace/models/` (HF cache)   |   rw    |     rw      |     —      |
| `/workspace/checkpoints/`         |   rw    |     rw      |     —      |
| `/root/.ssh/kurpatov-wiki-vault`  |   —     |      —      |     ro     |

Host paths:

- `${STORAGE_ROOT}/labs/wiki-ingest/sources/` — input source tree (video + audio + HTML).
- `${STORAGE_ROOT}/labs/wiki-ingest/vault/` — vault root. Contains
  `raw/` (a git working tree for the `kurpatov-wiki-raw` repo; its
  content lives under `raw/data/<course>/<module>/<stem>/`). The
  parallel `wiki/` layer is not created here — the wiki is authored
  and pushed from the operator's Mac (ADR 0007).
- `${STORAGE_ROOT}/models/` — shared HF cache with rl-2048.
- `~/.ssh/kurpatov-wiki-vault` — per-repo deploy key for the raw repo.

## Data contracts

### Inputs: `sources/`
Arbitrary directory hierarchy. Typical:

```
sources/
└── <course>/
    └── <module>/
        └── <lecture-name>.<ext>      # .mp4 | .mp3 | .mkv | .m4a | .html | …
```

Any depth of nesting is allowed — both the watcher and the incremental
script mirror the structure (see ADR 0004). The set of accepted suffixes
is the `INGEST_EXTENSIONS` allow-list — the union of `WHISPER_EXTENSIONS`
(video: `mp4/mkv/webm/mov/m4v/avi`; audio: `mp3/m4a/wav/ogg/flac/opus/aac`)
and `HTML_EXTENSIONS` (`html/htm`). faster-whisper routes audio through
ffmpeg internally, so any format ffmpeg can decode works; HTML takes the
`_extract_html.py` path (lecturer prose only, see ADR 0008). We gate
which extensions the watcher picks up; everything else is ignored.

### RAW layer: `vault/raw/data/<same dirs>/<stem>/raw.json`
The output slug is always `<stem>` (the source filename with its
extension stripped), regardless of extractor. Uniqueness within a
module is enforced one level up by the zero-padded `NNN` prefix every
source carries (ADR 0004). Stable contract (see ADR 0002
"JSON-only, single file"):

```json
{
  "info": {
    "language": "ru",
    "duration": 3210.12,
    "language_probability": 0.98,
    "source_path": "/workspace/sources/Psychologist-consultant/.../005 ... .mp4",
    "model": "large-v3",
    "compute_type": "float16",
    "beam_size": 5,
    "extractor": "whisper",
    "extracted_at": "2026-04-19T08:30:00Z",
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

- `info.extractor` — `"whisper"` or `"html"`. Distinguishes the two
  extractor paths without string-matching on `source_path`. HTML-produced
  raws carry `info.title` (lesson title) and `info.paragraph_count`; they
  do not carry `info.duration`, `info.model`, timing fields on segments,
  speaker, or words[]. See ADR 0008 for the full schema matrix.
- `info.source_path` — absolute path inside the container. Needed for:
  migration (`migrate_vault_hierarchy.py`), and for binding wiki pages back
  to their source media/page later.
- `info.diarized` — flag that `segments[].speaker` is populated. Currently
  always `false`; a later pyannote step will set it.
- Atomicity: the file is written to `<stem>.tmp/raw.json`, then the
  directory is renamed to `<stem>/`.

### WIKI layer: `kurpatov-wiki-wiki` (GitHub-canonical, Mac-authored)

Unlike the RAW layer, the wiki layer is **not** written from the server.
Full decision record: [ADR 0007](docs/adr/0007-wiki-layer-mac-side.md).
Authoring happens in a Claude Desktop (Cowork) session on the operator's
Mac, which reads the `kurpatov-wiki-raw` repo and writes the
`kurpatov-wiki-wiki` repo directly. `${STORAGE_ROOT}/labs/wiki-ingest/vault/
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
    ├── index.md                  course/module/source order + A-Z concept index
    ├── concept-index.json        authoritative authoring state (see below)
    ├── concepts/
    │   ├── _template.md
    │   ├── <concept-slug>.md     one per psychological concept
    │   └── ...
    └── sources/
        ├── _template.md
        └── <course>/<module>/<stem>.md   one per source (video or audio)
```

Two article types (see ADR 0007):

- **Source article** — four load-bearing sections in order:
  `## TL;DR` (1-2 sentences), `## Claims — provenance and fact-check`
  (every substantive claim marked with exactly one of
  `NEW` / `REPEATED (from: <slug>)` /
  `CONTRADICTS EARLIER (in: <slug>)` / `CONTRADICTS FACTS`; the last
  carries an external primary-source citation — peer-reviewed paper
  → textbook → reference site, with Wikipedia allowed only as a
  pointer),
  `## New ideas (verified)` (the filtered output: only pure-`NEW`
  claims that survived fact-check — the fast-reader's trusted path),
  `## All ideas` (full ideational content grouped by concept, with
  each bullet tagged `[NEW]` / `[REPEATED]` /
  `[CONTRADICTS EARLIER]` / `[CONTRADICTS FACTS]` and cross-linked
  to `concepts/`). Frontmatter carries `slug`, `course`, `module`,
  `extractor`, `source_raw`, `processed_at`, `concepts_touched`,
  `concepts_introduced`, `fact_check_performed` (boolean — did this
  pass consult external sources). There is no numeric `order:`
  field — module names are zero-padded (`05-conflicts`) and stems
  carry zero-padded numeric prefixes (`005 Conflict nature`), so
  sorted-path order equals course order (see ADR 0007 invariants).
  The four-way classification + fact-check pass was added on
  2026-04-24 — see ADR 0007 amendment.

- **Concept article** — an append-only article per psychological
  concept. A short top-of-article definition, followed by a
  "Contributions by source" log where each entry names a source slug
  and summarizes what that source adds to the concept. Never
  rewritten destructively; contradictions from a later source are
  recorded inside the *new* entry by quoting both sides, leaving
  the earlier entry untouched. Fixes to genuinely wrong prior
  content are explicit edits with reasons.

`data/concept-index.json` is the authoring state file (ADR 0007 →
Invariants). Every Mac-side session reads it at start, uses it to
decide what's "new" in the next source, and commits the updated
version at the end. Drift between this file and the `data/concepts/`
directory is a bug; the wiki-repo playbook at
`kurpatov-wiki-wiki/docs/authoring.md` spells out how to detect
and repair it. The forge-side mirror lives at
[docs/mac-side-wiki-authoring.md](docs/mac-side-wiki-authoring.md).

### Published repos

| GitHub repo             | Pushed by                               | Working tree                                         |
| ----------------------- | --------------------------------------- | ---------------------------------------------------- |
| `kurpatov-wiki-raw`     | `kurpatov-wiki-raw-pusher` (container)  | server: `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/`   |
| `kurpatov-wiki-wiki`    | Claude Desktop / Cowork session         | Cowork session workspace: `~/repos/kurpatov-wiki-wiki/` (by convention)        |

In the `kurpatov-wiki-raw` repo, raw transcripts live under a
`data/` subtree: `data/<course>/<module>/<stem>/raw.json`. The repo
root is reserved for future meta files. On the server the git
working tree sits at `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/` and
the pusher's `--raw` (watch subtree) points at
`${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/data/`. See ADR 0005.

In the `kurpatov-wiki-wiki` repo, content lives under `data/`
(articles, concept-index, nav); meta (CLAUDE.md, README, prompts/,
docs/) lives at the root. See ADR 0007.

## Invariants

1. **Ingest is idempotent.** If `raw.json` for a source exists and
   is not corrupt, both scripts (02 and 03) skip it.
2. **Hierarchy is mirrored under `data/`.**
   `out_dir = vault/raw/data / out_slug_for(source)` — for media that's
   `source.relative_to(sources).with_suffix("")`, for HTML it keeps the
   `.html` suffix in the slug (ADR 0008). The old flat layout is
   considered incompatible; migrate with `migrate_vault_hierarchy.py`
   (see ADR 0004). The `data/` prefix is per ADR 0005's
   data/content-split amendment.
3. **Only one GPU consumer at a time.** Jupyter and the ingest daemon
   share one GPU (`KURPATOV_WIKI_GPU_UUID`), but the ingest daemon
   unloads its model while idle so jupyter can use the memory for
   experiments (see ADR 0003). HTML ingest never touches the GPU;
   PDF ingest only touches it when the OCR fallback fires (image-only
   scans), and it unloads on idle like whisper does.
4. **File stability before processing.** The watcher waits until the
   source file's size and mtime stop changing for `--stable-sec` seconds
   (default 10). This protects against processing a half-copied file from
   rsync/scp/cp.
5. **Model format is fixed.** `large-v3`, `float16`, `beam=5`,
   `language=ru`, word timestamps, VAD with `min_silence_duration_ms=500`.
   Any deviation requires a SPEC update and most likely a migration — the
   config is recorded in `info` so transcripts of different "generations"
   can be told apart later.

## Status
Production for the RAW layer. Running since April 2026.

Done:
- Three roles in compose (jupyter + ingest + raw-pusher).
- Reactive watcher with lazy-load / idle-unload of the whisper model;
  HTML extraction dispatched inline on the same watcher (see ADR 0008).
- Strict slug-order processing (priority queue in the daemon, unified
  sorted loop in the batch script) so downstream stages always see
  `000/*` before `001/*` before `002/*`, regardless of extractor type
  or arrival order (see ADR 0008 amendment, 2026-04-21).
- Full mirror of the sources → vault/raw/data hierarchy.
- Migration script for the flat layout (ADR 0004); subsequent
  data/-subtree migration via the server-side script documented in
  ADR 0005's amendment.
- Continuous auto-push of `vault/raw/data/` to the
  `kurpatov-wiki-raw` private GitHub repo, with debounced commits
  (see ADR 0005).

Not yet:
- Diarization (pyannote). Placeholder in the format is there; the HF token
  hasn't been obtained.
- LLM summary per source (design: ADR 0007; content: Mac-side Claude
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
# Drop sources in (any INGEST_EXTENSIONS suffix — media, HTML, or PDF):
mkdir -p ${STORAGE_ROOT}/labs/wiki-ingest/sources/Psychologist-consultant/05-conflicts
cp ~/downloads/*.mp4 ${STORAGE_ROOT}/labs/wiki-ingest/sources/Psychologist-consultant/05-conflicts/
# or .mp3 / .m4a / .html / .pdf / … — same path.

# Bring up (from the forge root):
make kurpatov-wiki

# The watcher picks them up on its own. Batch pass over everything missing:
docker exec -t jupyter-kurpatov-wiki \
  python -u /workspace/notebooks/02_ingest_incremental.py
```

See also: `docs/adr/0001` through `0009`,
`docs/mac-side-wiki-authoring.md` (wiki-layer playbook),
`prompts/per-source-summarize.md`, `prompts/concept-article.md`,
`notebooks/02_ingest_incremental.py`,
`notebooks/03_watch_and_ingest.py`,
`notebooks/04_watch_raw_and_push.py`,
`notebooks/_extract_html.py`,
`notebooks/_extract_pdf.py`,
`notebooks/migrate_vault_hierarchy.py`.
