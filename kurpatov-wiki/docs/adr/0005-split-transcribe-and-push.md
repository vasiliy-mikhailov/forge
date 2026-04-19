# ADR 0005 — split transcription and git-push into two containers

## Status
Accepted (2026-04-19). Partially amends ADR 0001 ("two-layer vault"): the
two layers `raw/` and `wiki/` are now two *separate git repos* rather than
two sibling folders inside one repo. The vault filesystem layout under
`${STORAGE_ROOT}/kurpatov-wiki/vault/` is unchanged.

Amended (2026-04-19) by [ADR 0006](0006-lean-pusher-image.md): the
"They run the same image (`forge-kurpatov-wiki:latest`)" note below is
now obsolete. The pusher runs a dedicated lean image
(`forge-kurpatov-wiki-pusher:latest`, based on `python:3.12-slim`). The
container split itself is unchanged.

Amended (2026-04-19 — data/ content split). Paths below that place
content directly at the `vault/raw/` tree top level are now off by
one `data/` segment. The transcriber writes to
`/workspace/vault/raw/data/<course>/<module>/<stem>/raw.json`; the
pusher watches `/workspace/vault/raw/data/` while keeping its git
working tree (`--vault`) at `/workspace/vault/raw/` so the existing
`.git/` at that root keeps working. The `kurpatov-wiki-raw` repo's
top level now contains a `data/` directory; course / module / stem
dirs live under it. Rationale: course and module names are
unconstrained strings; a tooling addition at the repo root (e.g. a
future `README.md`, `CLAUDE.md`, or CI config) would collide with a
course slug in the same namespace. Mirrors the same split landed
in `kurpatov-wiki-wiki` under ADR 0007's first amendment. The ADR
body below describes the post-migration layout; the pre-amendment
state survives only in git history.

## Context
Once the RAW layer stabilized (ADR 0002), I wanted the transcripts to be
continuously mirrored to a private GitHub repo — as a backup, and as a
cheap "has something new landed?" view from anywhere. The first design
folded the `git add/commit/push` call into the transcriber itself, at the
end of each successful transcription.

That turned out to be wrong for two reasons:

1. **Single responsibility.** The transcriber is a GPU job. A failing
   network / DNS / SSH key issue at git-push time should not mark a
   transcription as failed, tie up GPU memory waiting on a remote, or
   leak git config into a notebook image whose primary job is whisper.
2. **Bursty writes vs. commit cadence.** A single video produces one
   `raw.json`, but a batch upload produces N of them over a few minutes.
   One commit per file is noisy; batching by "filesystem has been quiet
   for X seconds" is the right cadence, and that belongs in a watcher,
   not in the transcriber's inner loop.

At the same time, the original ADR 0001 assumed `raw/` and `wiki/` would
eventually coexist inside one repository. That stopped making sense as
soon as publishing got real:

- `raw/` is produced by a deterministic GPU pipeline (faster-whisper +
  pinned model). It is machine-generated, high-volume, rarely of
  interest to a human reader.
- `wiki/` is produced by LLM summarization + hand-curation. It is the
  thing I actually want to publish and browse.

Mixing them in one repo forces one set of push permissions, one set of
commit noise, one README, one set of downstream consumers. Separating
them costs nothing on disk and buys clean boundaries at every other
layer.

## Decision

### Two containers, not one
Under the kurpatov-wiki compose project there are now two separate
single-responsibility services sharing only the vault filesystem via a
Docker volume:

```
kurpatov-transcriber         watches  /workspace/videos/
                             writes   /workspace/vault/raw/data/
                                        <course>/<module>/<stem>/raw.json
                             knows nothing about git.

kurpatov-wiki-raw-pusher     watches  /workspace/vault/raw/data/  (--raw)
                             runs     git -C /workspace/vault/raw/  (--vault)
                                        add -A && git commit && git push
                             knows nothing about whisper, GPUs, or videos.
                             No GPU reservation — CPU only.
```

The pusher separates *what it watches* (`--raw`, the content
subtree) from *what it commits in* (`--vault`, the git working
tree). The split exists precisely so the `data/` migration could
move content without moving `.git/`: `vault/raw/.git/` stays put,
`git add -A` at the working-tree root picks up the moved content
naturally, and the watcher's debounce logic only fires on actual
content changes under `data/`.

~~They run the same image (`forge-kurpatov-wiki:latest`) because
`openssh-client` + Python are already in it; no separate Dockerfile.~~
**Superseded by ADR 0006.** The transcriber still runs
`forge-kurpatov-wiki:latest`; the pusher now runs a dedicated lean
image `forge-kurpatov-wiki-pusher:latest` built from
`kurpatov-wiki/Dockerfile.pusher` (`python:3.12-slim` + git +
openssh-client + watchdog, ~200 MB).

### Two repos, not one
`raw/` and `wiki/` live in two distinct private GitHub repos:

| Repo                    | Contents                                                    | Pushed by                     |
| ----------------------- | ----------------------------------------------------------- | ----------------------------- |
| `kurpatov-wiki-raw`     | `data/<course>/<module>/<stem>/raw.json`                    | `kurpatov-wiki-raw-pusher`    |
| `kurpatov-wiki-wiki`    | `data/videos/<course>/<module>/<stem>.md`, `data/concepts/` | Mac-side Cowork session (ADR 0007) |

The names `raw` / `wiki` follow the vault layers from ADR 0001. The
`-wiki-wiki` suffix looks odd but matches: the subsystem is
`kurpatov-wiki` and the repo holds its `wiki/` layer.

### Repo top level is `data/`, not the content directly
On the server, `${STORAGE_ROOT}/kurpatov-wiki/vault/raw/` is a git
working tree. Its `.git/` sits at that directory; the repo's top
level is a `data/` subtree that holds
`<course>/<module>/<stem>/raw.json`. There is no sibling `wiki/`
layer in this repo — that lives in `kurpatov-wiki-wiki`. The parent
`vault/` directory exists only as a convenience for operators and
retains its legacy on-disk name (cheap to rename later).

The `data/` segment exists so that future top-level tooling files
(`README.md`, `CLAUDE.md`, CI config) cannot collide with a course
directory named `README` or `CLAUDE`. Same rationale as the wiki
repo's split (ADR 0007).

### Deploy keys, one per repo
Each repo has its own SSH deploy key on GitHub. On the host, keys live
at `~/.ssh/kurpatov-wiki-vault` (legacy filename — matches the current
`core.sshCommand` inside `vault/raw/.git/config`; cheap to rename out
of band). The key is mounted into the pusher container read-only at
`/root/.ssh/kurpatov-wiki-vault`. The transcriber does not see any
key — it has no reason to.

### Debounce + ignore staging dirs
The pusher uses `watchdog` to subscribe to filesystem events over
`/workspace/vault/raw/data/` recursively (`--raw`), bumps a debounce
deadline on every event, and fires
`git -C /workspace/vault/raw/ add -A && git commit && git push` (the
commit runs from the `--vault` root, which is the git working tree)
once the tree has been quiet for `--debounce-sec` seconds (default
10). Any path passing through a `.tmp` sibling is ignored — that's
the transcriber's atomic-write staging area (ADR 0002); the rename
itself generates an event for the final directory, which the pusher
picks up naturally.

### Identity and safe.directory
The pusher runs as root in the container but the `.git` tree on the
host is owned by `vmihaylov`. Rather than configure git globally
inside the image, the pusher passes `safe.directory`, `user.name`,
and `user.email` inline on every `git` invocation via `-c` flags.
No mutable git config is written into the mounted `.git`.

## Consequences
- Plus: a git-push failure (bad network, expired key, remote down)
  cannot stall transcription or block GPU memory.
- Plus: the transcriber image keeps its single concern; the pusher
  reuses the same image without changing its responsibility.
- Plus: independent commit cadence per repo — `raw` is machine-paced,
  `wiki` is human-paced, and they can't step on each other.
- Plus: different access policies per repo. `kurpatov-wiki-wiki` can
  eventually go public or move to GitHub Pages without exposing
  multi-GB of raw transcripts.
- Plus: independent backup/retention — `raw` is easy to regenerate in
  principle (re-run the GPU pipeline); `wiki` is the precious artifact.
- Minus: one more container to keep alive, one more log stream to
  watch. Mitigated by making the pusher log idle-but-alive at INFO
  (`[git  ] nothing to commit`) so a silent daemon is visibly wrong.
- Minus: two deploy keys to rotate instead of one.

## Invariants
- The transcriber must never invoke `git` on its own. If something
  wants transcripts mirrored, it goes through the pusher — or through
  a future replacement that also listens on `/workspace/vault/raw/`.
- The raw-pusher must never read or write anything outside
  `/workspace/vault/raw/` (its `--vault` working tree, which
  includes the `data/` content subtree it actually watches) and the
  mounted deploy key. It has no business touching videos, models,
  or the wiki layer.
- `vault/raw/.git/` stays on the host, not in the container image.
  The container is stateless; rebuilding it must not invalidate or
  rewrite repo history.
- `<stem>.tmp/` paths are invisible to the pusher. A commit must only
  ever include complete `<stem>/raw.json` files.

## Alternatives considered
- **One container doing both.** Rejected — rationale above (mixing GPU
  work with network work, and a failed push blocking transcription).
- **Cron-based pusher instead of watchdog.** Rejected for the same
  reason ADR 0003 rejected cron for transcription: reactive avoids
  both the "wait a full cycle" latency and the "cron fires mid-write"
  race.
- **One repo holding both raw and wiki.** Rejected — ADR 0001's two
  layers were always meant to have different lifecycles and different
  audiences; conflating them into one repo's `raw/` + `wiki/` siblings
  gave up those distinctions without buying anything.
- **Push from outside docker (systemd timer on the host).** Rejected —
  the on-server deploy key and the git tree already live at a container
  path; duplicating that on the host to support a host-side pusher
  adds more coupling than it removes.

## Follow-ups
- Rename the on-disk dir `${STORAGE_ROOT}/kurpatov-wiki/vault/` and the
  deploy key file `~/.ssh/kurpatov-wiki-vault` away from the legacy
  "vault" name. Cheap but touches live state; deferred until
  convenient.
- ~~Wire up the `kurpatov-wiki-wiki` repo when wiki assembly exists
  (task #7). Likely a second pusher container, same shape.~~
  **Superseded by ADR 0007.** The wiki repo is pushed by a Mac-side
  Cowork session, not a server-side pusher. The symmetry with ADR
  0005 holds at a different layer (session-as-pusher vs.
  container-as-pusher).
- Consider signing commits once the pusher is no longer experimental.
