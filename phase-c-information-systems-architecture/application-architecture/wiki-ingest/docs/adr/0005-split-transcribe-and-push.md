# ADR 0005 — split transcription and git-push into two containers

## Status

Accepted (2026-04-19). Active.

## Context

Once the RAW layer stabilised (ADR 0002), transcripts needed to be
continuously mirrored to a private GitHub repo — as a backup, and as
a cheap "has something new landed?" view from anywhere. The first
design folded the `git add/commit/push` call into the ingest daemon
itself, at the end of each successful transcription.

That turned out to be wrong for two reasons:

1. **Single responsibility.** The ingest daemon is a GPU job. A
   failing network / DNS / SSH key issue at git-push time should
   not mark a transcription as failed, tie up GPU memory waiting on
   a remote, or leak git config into a notebook image whose primary
   job is whisper.
2. **Bursty writes vs. commit cadence.** A single source produces
   one `raw.json`, but a batch upload produces N of them over a few
   minutes. One commit per file is noisy; batching by "filesystem
   has been quiet for X seconds" is the right cadence, and that
   belongs in a watcher, not in the ingest daemon's inner loop.

At the same time, the original ADR 0001 assumed `raw/` and `wiki/`
would eventually coexist inside one repository. That stopped making
sense as soon as publishing got real:

- `raw/` is produced by a deterministic GPU pipeline
  (faster-whisper + pinned model, plus a second extractor for HTML
  / PDF — see [ADR 0008](0008-ingest-dispatch.md)). It is
  machine-generated, high-volume, rarely of interest to a human
  reader.
- `wiki/` is produced by LLM summarisation + hand curation. It is
  the artefact intended for browsing.

Mixing them in one repo forces one set of push permissions, one
set of commit noise, one README, one set of downstream consumers.
Separating them costs nothing on disk and buys clean boundaries at
every other layer.

## Decision

### Two containers, not one

Under the wiki-ingest lab there are two single-responsibility
services sharing only the vault filesystem via a Docker volume:

```
kurpatov-ingest              watches  /workspace/sources/
                             writes   /workspace/vault/raw/data/
                                        <course>/<module>/<stem>/raw.json
                             knows nothing about git.

kurpatov-wiki-raw-pusher     watches  /workspace/vault/raw/data/  (--raw)
                             runs     git -C /workspace/vault/raw/  (--vault)
                                        add -A && git commit && git push
                             knows nothing about whisper, GPUs, or source media.
                             No GPU reservation — CPU only.
```

The pusher separates *what it watches* (`--raw`, the content
subtree) from *what it commits in* (`--vault`, the git working
tree). The split exists precisely so content can move under
`data/` without moving `.git/`: `vault/raw/.git/` stays put,
`git add -A` at the working-tree root picks up moved content
naturally, and the watcher's debounce logic only fires on actual
content changes under `data/`.

The two containers run different images. The ingest daemon runs
`forge-kurpatov-wiki:latest` (the full image with whisper + Python
+ extractors). The pusher runs a dedicated lean image
`forge-kurpatov-wiki-pusher:latest` built from
`wiki-ingest/Dockerfile.pusher` (`python:3.12-slim` + git +
openssh-client + watchdog, ~200 MB). See
[ADR 0006](0006-lean-pusher-image.md) for the lean-pusher
rationale.

### Two repos, not one

`raw/` and `wiki/` live in two distinct private GitHub repos:

| Repo                    | Contents                                                    | Pushed by                     |
| ----------------------- | ----------------------------------------------------------- | ----------------------------- |
| `kurpatov-wiki-raw`     | `data/<course>/<module>/<stem>/raw.json`                    | `kurpatov-wiki-raw-pusher`    |
| `kurpatov-wiki-wiki`    | `data/sources/<course>/<module>/<stem>.md`, `data/concepts/` | Mac-side Cowork session ([ADR 0007](0007-wiki-layer-mac-side.md)) |

The names `raw` / `wiki` follow the vault layers from ADR 0001.
The `-wiki-wiki` suffix looks odd but matches: the subsystem is
`kurpatov-wiki` and the repo holds its `wiki/` layer. The
asymmetry between the two pushers (server-side container vs.
Mac-side session) is intentional — the wiki layer benefits from
running close to the editor doing curation; the raw layer must run
where the GPU and the storage are.

### Repo top level is `data/`, not the content directly

On the server, `${STORAGE_ROOT}/labs/wiki-ingest/vault/raw/` is a
git working tree. Its `.git/` sits at that directory; the repo's
top level is a `data/` subtree that holds
`<course>/<module>/<stem>/raw.json`. There is no sibling `wiki/`
layer in this repo — that lives in `kurpatov-wiki-wiki`. The
parent `vault/` directory exists only as a convenience for
operators and retains its legacy on-disk name (cheap to rename
later).

The `data/` segment exists so that future top-level tooling files
(`README.md`, `CLAUDE.md`, CI config) cannot collide with a course
directory named `README` or `CLAUDE`. Same rationale as the wiki
repo's split (ADR 0007).

### Deploy keys, one per repo

Each repo has its own SSH deploy key on GitHub. On the host, keys
live at `~/.ssh/kurpatov-wiki-vault` (legacy filename — matches
the current `core.sshCommand` inside `vault/raw/.git/config`;
cheap to rename out of band). The key is mounted into the pusher
container read-only at `/root/.ssh/kurpatov-wiki-vault`. The
ingest daemon does not see any key — it has no reason to.

### Debounce + ignore staging dirs

The pusher uses `watchdog` to subscribe to filesystem events over
`/workspace/vault/raw/data/` recursively (`--raw`), bumps a
debounce deadline on every event, and fires
`git -C /workspace/vault/raw/ add -A && git commit && git push`
(the commit runs from the `--vault` root, which is the git
working tree) once the tree has been quiet for `--debounce-sec`
seconds (default 10). Any path passing through a `.tmp` sibling
is ignored — that's the ingest daemon's atomic-write staging area
(ADR 0002); the rename itself generates an event for the final
directory, which the pusher picks up naturally.

### Identity and safe.directory

The pusher runs as root in the container but the `.git` tree on
the host is owned by `vmihaylov`. Rather than configure git
globally inside the image, the pusher passes `safe.directory`,
`user.name`, and `user.email` inline on every `git` invocation
via `-c` flags. No mutable git config is written into the mounted
`.git`.

## Consequences

- Plus: a git-push failure (bad network, expired key, remote down)
  cannot stall transcription or block GPU memory.
- Plus: each image keeps its single concern — whisper / GPU vs.
  git / network — and they can be sized + base-imaged separately
  (the lean pusher is ~200 MB vs. the multi-GB GPU image).
- Plus: independent commit cadence per repo — `raw` is
  machine-paced, `wiki` is human-paced, and they cannot step on
  each other.
- Plus: different access policies per repo. `kurpatov-wiki-wiki`
  can eventually go public or move to GitHub Pages without
  exposing multi-GB of raw transcripts.
- Plus: independent backup/retention — `raw` is easy to regenerate
  in principle (re-run the GPU pipeline); `wiki` is the precious
  artifact.
- Minus: one more container to keep alive, one more log stream to
  watch. Mitigated by making the pusher log idle-but-alive at
  INFO (`[git  ] nothing to commit`) so a silent daemon is
  visibly wrong.
- Minus: two deploy keys to rotate instead of one.

## Invariants

- The ingest daemon must never invoke `git` on its own. If
  something wants transcripts mirrored, it goes through the pusher
  — or through a future replacement that also listens on
  `/workspace/vault/raw/`.
- The raw-pusher must never read or write anything outside
  `/workspace/vault/raw/` (its `--vault` working tree, which
  includes the `data/` content subtree it actually watches) and
  the mounted deploy key. It has no business touching source
  media, models, or the wiki layer.
- `vault/raw/.git/` stays on the host, not in the container image.
  The container is stateless; rebuilding it must not invalidate
  or rewrite repo history.
- `<stem>.tmp/` paths are invisible to the pusher. A commit must
  only ever include complete `<stem>/raw.json` files.

## Alternatives considered

- **One container doing both.** Rejected — rationale above (mixing
  GPU work with network work, and a failed push blocking
  transcription).
- **Cron-based pusher instead of watchdog.** Rejected for the same
  reason ADR 0003 rejected cron for transcription: reactive avoids
  both the "wait a full cycle" latency and the "cron fires
  mid-write" race.
- **One repo holding both raw and wiki.** Rejected — ADR 0001's
  two layers were always meant to have different lifecycles and
  different audiences; conflating them into one repo's `raw/` +
  `wiki/` siblings gave up those distinctions without buying
  anything.
- **Push from outside docker (systemd timer on the host).**
  Rejected — the on-server deploy key and the git tree already
  live at a container path; duplicating that on the host to
  support a host-side pusher adds more coupling than it removes.

## Follow-ups

- Rename the on-disk dir `${STORAGE_ROOT}/labs/wiki-ingest/vault/`
  and the deploy key file `~/.ssh/kurpatov-wiki-vault` away from
  the legacy "vault" name. Cheap but touches live state; deferred
  until convenient.
- Consider signing commits once the pusher is no longer
  experimental.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain inherited from the lab's AGENTS.md.
