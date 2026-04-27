# kurpatov-wiki-ingest — agent context

This file follows the same Phase A-H structure as forge-level
`AGENTS.md`. Read forge-level first for cross-cutting rules; this
file is scoped to the ingest lab.

## Phase A — Vision (lab-scoped)

This lab provides the **media → raw transcript** pipeline. Every
Курпатов lecture starts as audio/video; this lab turns it into
whisper-segment JSON that downstream labs (bench, compiler) consume
to produce wiki articles. Ingest is the first step in the wiki
product's collect/filter/adapt mechanism.

## Phase B — Capabilities + quality dimensions

| Capability                     | Quality dimension                                  |
|--------------------------------|----------------------------------------------------|
| Audio → text transcription     | Accuracy on Russian speech (Курпатов register)     |
| Raw-data publication           | Fresh raw.json visible to downstream labs ≤ N min after audio drops |
| Append-only raw-source archive | No source ever silently mutates after publication  |

## Phase C — Data shapes

- **Input:** audio/video files in `${STORAGE_ROOT}/labs/kurpatov-wiki-ingest/vault/raw/data/<course>/<module>/<source>/source.mp3` (or `.mp4`).
- **Output:** whisper-segment JSON at the same path replacing
  `source.mp3` with `raw.json`:
  ```
  {
    "info": {
      "extractor": "whisper",
      "language": "ru",
      "duration": <float seconds>,
      "source_path": "data/<course>/<module>/<source>/source.mp3"
    },
    "segments": [
      {"start": <float>, "end": <float>, "text": "<utterance>"},
      ...
    ]
  }
  ```
- **Append-only invariant:** once `raw.json` is committed to the
  `kurpatov-wiki-raw` GitHub repo, the format and content never
  change in place. Re-transcribing means a new run identifier, not
  overwriting.
- **The vault working tree is special:** `${STORAGE_ROOT}/labs/kurpatov-wiki-ingest/vault/raw/`
  is a git checkout of the *separate* `kurpatov-wiki-raw` repo
  (NOT a subdirectory of forge). The `raw-pusher` container commits
  + pushes from there. See ADR
  `labs/kurpatov-wiki-ingest/docs/adr/0005-split-transcribe-and-push.md`.

## Phase D — Tech services this lab provides + components

**Service: Audio → text transcription** (consumer:
`kurpatov-wiki-wiki` source-of-truth, eventually populated through
ingest into compiler/bench).

- Component: faster-whisper (Russian language).
- Component: a watcher container (`03_watch_and_transcribe.py`) that
  polls the vault for new audio and transcribes incrementally.
- Component: `raw-pusher` container that commits + pushes new
  `raw.json` to the `kurpatov-wiki-raw` GitHub remote.
- Component: caddy 2 (reverse proxy / TLS for any UI; mostly idle).
- Component: docker-compose (orchestrates whisper-watcher +
  raw-pusher + caddy).

L1: ~200 lectures (Курпатов "Психолог-консультант" course modules
000-006 and beyond) transcribed end-to-end. Output is the canonical
`raw.json` shape consumed downstream.

L2: stable; not currently on the active trajectory.

## Phase E/F — Active trajectories

(None active. Ingest is in steady state.)

## Phase G — Lab-local operational rules

- **GPU choice:** the RTX 5090 hosts ingest. The Blackwell hosts
  compiler (or rl-2048, when active). Don't reassign without an ADR.
- **`raw.json` shape is load-bearing.** Every downstream layer
  (bench's `extract_transcript.py`, the orchestrator, eval metrics)
  parses `info.duration` and `segments[].{start,end,text}`. Schema
  changes require an ADR + downstream consumer review.
- **The vault `raw/` checkout is not a forge subdirectory.** It's a
  git working tree of the `kurpatov-wiki-raw` repo. Don't `git`
  operations on it from forge tooling — go through the `raw-pusher`
  container, which has the correct identity + push token.
- **Whisper model pinning.** The model variant (e.g.
  `large-v3-russian-distilled`) is pinned via env var. Don't
  silently switch — accuracy regressions affect every downstream
  metric.
- **Watcher idempotency.** If the watcher restarts mid-job, it must
  resume cleanly. Re-transcribing already-`raw.json`'d sources is
  forbidden (append-only invariant).

## Phase H — Trajectories

| Capability | Level 1 (today) | Level 2 (next) | Metric delta |
|------------|-----------------|----------------|--------------|
| Audio → text transcription | ~200 lectures, faster-whisper, append-only | (stable) | (none active) |
| Raw-data publication | watcher + raw-pusher, ~minutes-from-audio-drop to GitHub commit | (stable) | (none active) |

## Cross-references

- Forge-level: `forge/CLAUDE.md` Phase D (service tenancy: ingest
  produces what bench consumes via the wiki repo).
- ADR for vault split: `docs/adr/0005-split-transcribe-and-push.md`.
- Schema is documented in `SPEC.md` of this lab.
