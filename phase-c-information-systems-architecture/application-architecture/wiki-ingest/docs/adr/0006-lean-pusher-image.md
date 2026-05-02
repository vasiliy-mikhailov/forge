# ADR 0006 — lean image for the raw-pusher

## Status
Accepted (2026-04-19). Amends ADR 0005 ("split transcription and git-push
into two containers"): the decision there to run both containers from a
single image is reversed. The split into two *containers* still stands.

## Context
ADR 0005 split the transcriber and the pusher into separate containers
for single-responsibility reasons but noted: "They run the same image
(`forge-kurpatov-wiki:latest`) because `openssh-client` + Python are
already in it; no separate Dockerfile." That was convenient at the time
and unambiguously wrong in hindsight. The shared image is
`nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04` plus CUDA-built PyTorch,
faster-whisper, pyannote, jupyterlab, etc. — around 20 GB.

Symptoms that surfaced once the pusher was live:

- Every `docker logs kurpatov-wiki-raw-pusher` opens with the NVIDIA
  CUDA banner:
  "CUDA Version is insufficient / GPU functionality will not be
  available." The pusher has no GPU reservation and doesn't want one;
  the banner is the CUDA image's startup message, printed because the
  container runs from a CUDA base without GPU devices attached. It's
  cosmetically annoying *and* was the real cause of the smoke-test
  `grep -q | pipefail` SIGPIPE false-fail documented in
  `tests/smoke.md` §6: the long banner kept `docker logs` producing
  output after `grep -q` had matched and closed stdin, failing the
  pipeline under `pipefail`.
- The pusher's working set is literally `python`, `git`,
  `openssh-client`, and the `watchdog` package. Carrying the CUDA
  toolchain, torch, whisper, pyannote, jupyter, and a venv for them is
  pure ballast on container start, image pull, image registry, and
  attack-surface audit.
- Rebuilds are slower than they need to be. A one-character change
  inside `04_watch_raw_and_push.py` shouldn't sit behind a 20 GB image
  rebuild if anything in the GPU layers invalidates.

## Decision

### Two images, not one

The kurpatov-wiki compose project builds and tags two images:

| Image                                 | Base                                            | Purpose                             |
| ------------------------------------- | ----------------------------------------------- | ----------------------------------- |
| `forge-kurpatov-wiki:latest`          | `nvidia/cuda:12.9.1-cudnn-devel-ubuntu24.04`    | jupyter + transcriber (GPU work)    |
| `forge-kurpatov-wiki-pusher:latest`   | `python:3.12-slim`                              | raw-pusher (git over SSH + watchdog) |

The pusher's Dockerfile is `kurpatov-wiki/Dockerfile.pusher`. It installs
only `git`, `openssh-client`, `ca-certificates` via apt, and `watchdog`
via pip. No venv, no torch, no CUDA, no jupyter. Expected built size:
around 200 MB.

### Compose wires the build automatically

`kurpatov-wiki/docker-compose.yml` declares the pusher service with
`build: { context: ., dockerfile: Dockerfile.pusher }` and
`image: forge-kurpatov-wiki-pusher:latest`. `make kurpatov-wiki-build`
runs `docker compose build` which walks every service with a `build:`
block, so both images come up together. No new Makefile target is
needed.

### Smoke test enforces the split

`scripts/smoke.sh` §7 asserts:

1. `docker inspect kurpatov-wiki-raw-pusher --format '{{.Config.Image}}'`
   returns an image that is **not** the same as the one used by
   `jupyter-kurpatov-wiki`.
2. `docker image inspect <pusher-image> --format '{{.Size}}'` is
   **under 500 MB**.

Model lives at `tests/smoke.md` §7; see that file for goal / signals /
edge cases. An accidental `FROM forge-kurpatov-wiki:latest` regression
in `Dockerfile.pusher` trips both assertions.

## Consequences

- Plus: the pusher's container start no longer prints a GPU warning for
  a daemon that does zero GPU work. Logs become actually-relevant.
  (Bonus: removes the accidental pressure that made smoke-test check
  #6 flaky under `pipefail` — see `tests/smoke.md` §6 edge cases.)
- Plus: image size drops from ~20 GB to ~200 MB for the pusher path.
  Faster pulls, less disk, smaller attack surface.
- Plus: rebuilds are decoupled — a change to Python transcription
  code no longer invalidates the pusher image layer cache, and a
  change to the pusher Dockerfile no longer invalidates the 20 GB GPU
  image.
- Plus: security posture improves: the pusher carries the deploy key
  and no longer sits alongside a large pile of ML dependencies with
  their own CVE churn.
- Minus: one more Dockerfile to keep in sync. Acceptable — the pusher
  Dockerfile is ~5 lines and changes roughly never.
- Minus: two images to push/pull to/from the local builder. Already
  handled by the compose layer; no new operator steps.

## Invariants

- `kurpatov-wiki-raw-pusher` must never `FROM` the GPU image.
  Violations are caught by `scripts/smoke.sh` §7 and by this ADR's
  existence; amending either silently is a policy smell.
- The pusher image must **not** grow torch, whisper, jupyter, CUDA, or
  any ML dependency. If something like `pygit2` ever makes the pusher
  cleaner or faster, that's fine; cryptography / ML is not.
- The smoke test's 500 MB threshold is the ceiling on "lean". Raising
  it requires updating `tests/smoke.md` §7 *first* with the reason.

## Alternatives considered

- **Keep sharing the image; silence the CUDA banner.** Rejected — the
  banner is emitted by `/opt/nvidia/entrypoint.d/...` scripts inside
  the CUDA base image. Silencing it per-service is brittle
  (depends on NVIDIA's script layout) and leaves the image-size /
  attack-surface problems untouched.
- **Put `openssh-client` + `git` into a separate "bastion" image and
  share it with a future secrets-handling container.** Premature — no
  second tenant for that image exists yet, and YAGNI. The pusher's
  Dockerfile is small enough to inline without a shared base layer.
- **Host-side push (cron/systemd on the host) to avoid the container
  image question entirely.** Rejected again (ADR 0005 rejected this on
  coupling grounds); nothing in the image-size issue reopens that.

## Follow-ups

- Verify `forge-kurpatov-wiki-pusher:latest` size empirically after
  the first rebuild; update `tests/smoke.md` §7 if 500 MB is either
  too loose or too tight.
- Whenever the `kurpatov-wiki-wiki` repo + its own pusher ship (ADR
  0005 follow-up, blocked on task #7), reuse
  `forge-kurpatov-wiki-pusher:latest` — it's the same shape of
  daemon.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain inherited from the lab's AGENTS.md.
