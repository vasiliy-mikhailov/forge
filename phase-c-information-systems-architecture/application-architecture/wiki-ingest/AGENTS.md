# wiki-ingest — agent context

This file follows the same Phase A-H structure as forge-level
`AGENTS.md`. Read forge-level first for cross-cutting rules; this
file is scoped to the ingest lab.

## Phase A — Architecture Vision

**Lab role within forge.** This lab is one of forge's four application components. It realises the following forge-level capabilities for the *audio-to-text* domain: **Service operation** (the watcher + raw-pusher pipeline) and **Product delivery** (append-only raw.json publication to the kurpatov-wiki-raw GitHub repo).

**Vision (lab-scoped).** Provide the audio→text pipeline that turns
Kurpatov's ~200 lectures into the `raw.json` shape every downstream
lab consumes. Ingest is the *collect* step in the wiki product's
collect/filter/adapt mechanism.

**Lab-scoped stakeholders.**

- **Architect of record** (forge-wide).
- **Downstream consumers** — `wiki-bench` (reads `raw.json`
  to compile wiki articles), `kurpatov-wiki-wiki` (the source-of-truth
  repo where compiled wiki articles cite raw paths).

**Lab-scoped drivers.**

- Volume: ~200 lectures, hours each. Manual transcription is
  intractable.
- Append-only invariant: once a `raw.json` is published, downstream
  consumers cite paths into it forever. Mutating in place breaks
  citations.

**Lab-scoped goals.**

- **Transcription accuracy** on Russian psychology register
  (Kurpatov has dense compound terms — `системно-поведенческая
  психотерапия` etc.). Quality dim: word-error rate on a held-out
  audit set.
- **Latency** from new audio drop to `raw.json` published in
  `kurpatov-wiki-raw` GitHub repo.

**Lab-scoped principles.**

- `raw.json` shape is load-bearing — schema change requires an ADR
  + downstream consumer review.
- Append-only: re-transcribing produces a new run identifier, never
  overwrites.
- The vault `raw/` checkout is a working tree of the
  `kurpatov-wiki-raw` repo, not a forge subdirectory; only the
  `raw-pusher` container performs git operations there.

## Phase B — Business Architecture

| Capability                     | Quality dimension                                  |
|--------------------------------|----------------------------------------------------|
| Audio → text transcription     | Accuracy on Russian speech (Курпатов register)     |
| Raw-data publication           | Fresh raw.json visible to downstream labs ≤ N min after audio drops |
| Append-only raw-source archive | No source ever silently mutates after publication  |

## Phase C — Information Systems Architecture

- **Input:** audio/video files in `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/data/<course>/<module>/<source>/source.mp3` (or `.mp4`).
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
- **The vault working tree is special:** `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/`
  is a git checkout of the *separate* `kurpatov-wiki-raw` repo
  (NOT a subdirectory of forge). The `raw-pusher` container commits
  + pushes from there. See ADR
  `phase-c-information-systems-architecture/application-architecture/wiki-ingest/docs/adr/0005-split-transcribe-and-push.md`.

**ADRs (Phase C scope).**
- [`docs/adr/0001-two-layer-vault.md`](docs/adr/0001-two-layer-vault.md) — two-layer vault (input media vs raw transcript).
- [`docs/adr/0002-raw-format-single-json.md`](docs/adr/0002-raw-format-single-json.md) — raw.json single-file whisper-segment shape.
- [`docs/adr/0004-mirror-sources-hierarchy.md`](docs/adr/0004-mirror-sources-hierarchy.md) — mirror sources hierarchy in vault/raw.
- [`docs/adr/0007-wiki-layer-mac-side.md`](docs/adr/0007-wiki-layer-mac-side.md) — wiki authoring layer on mac side.

## Phase D — Technology Architecture

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

**ADRs (Phase D scope).**
- [`docs/adr/0003-watcher-reactive-not-cron.md`](docs/adr/0003-watcher-reactive-not-cron.md) — reactive fanotify watcher, not cron.
- [`docs/adr/0005-split-transcribe-and-push.md`](docs/adr/0005-split-transcribe-and-push.md) — split transcribe and push containers.
- [`docs/adr/0006-lean-pusher-image.md`](docs/adr/0006-lean-pusher-image.md) — lean pusher image (separate from transcriber).
- [`docs/adr/0009-pdf-extractor.md`](docs/adr/0009-pdf-extractor.md) — pdf-extractor component.

## Phase E — Opportunities and Solutions

Gap analysis for this lab — what capabilities are not yet at Level 2.
If a `STATE-OF-THE-LAB.md` exists, it is the canonical gap audit;
otherwise the Phase H trajectories table below stands in.

## Phase F — Migration Planning

Active experiment specs at `docs/experiments/<id>.md` are the
sequenced work packages closing those gaps. Only Active and
Closed-but-still-cited experiments are kept; superseded ones go to
git history per Phase H.


(None active. Ingest is in steady state.)

## Phase G — Implementation Governance

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

**ADRs (Phase G scope).**
- [`docs/adr/0008-ingest-dispatch.md`](docs/adr/0008-ingest-dispatch.md) — Make dispatcher for per-source ingest.

## Phase H — Architecture Change Management

| Capability | Level 1 (today) | Level 2 (next) | Metric delta |
|------------|-----------------|----------------|--------------|
| Audio → text transcription | ~200 lectures, faster-whisper, append-only | (stable) | (none active) |
| Raw-data publication | watcher + raw-pusher, ~minutes-from-audio-drop to GitHub commit | (stable) | (none active) |

## Cross-references

- Forge-level: `forge/AGENTS.md` Phase D (service tenancy: ingest
  produces what bench consumes via the wiki repo).
- ADR for vault split: `docs/adr/0005-split-transcribe-and-push.md`.
- Schema is documented in `SPEC.md` of this lab.
