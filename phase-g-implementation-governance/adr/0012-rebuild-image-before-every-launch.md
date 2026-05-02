# ADR 0012 — Rebuild the bench image before every test or pilot launch

Status: Accepted
Date: 2026-04-29
Phase: G (implementation governance)
Related: P3 (containers-only execution), ADR 0010 (test fidelity), ADR 0011 (NFC/NFD)

## Context

The bench image `kurpatov-wiki-bench:1.17.0-d8-cal` bakes the orchestrator
scripts into `/opt/forge/`:

```
COPY orchestrator/run-d8-pilot.py /opt/forge/run-d8-pilot.py
COPY orchestrator/embed_helpers.py /opt/forge/embed_helpers.py
COPY evals/grade/bench_grade.py    /opt/forge/bench_grade.py
```

The image was last built weeks ago. Recent edits to those scripts landed
on the host filesystem (and in git) but **not** in the image. The previous
runner pattern was:

```
docker run \
  -v $HOST/run-d8-pilot.py:/opt/forge/run-d8-pilot.py \
  -v $HOST/embed_helpers.py:/opt/forge/embed_helpers.py \
  kurpatov-wiki-bench:1.17.0-d8-cal ...
```

— bind-mount the host's current copy over the baked one. This works for
files that are listed. The runner that drove e2e #2 listed `run-d8-pilot.py`
and `embed_helpers.py` but not `bench_grade.py`. The result: the
orchestrator inside the container ran my up-to-date code but called a
**stale** `bench_grade.py` from the image, which rejected the new
`--single-source-stem` flag, exited with empty stdout, and surfaced as
`non-JSON: ` verify-fail. ~30 minutes of investigation; 100% silent skew.

The pattern is fragile by construction: every new script in `/opt/forge/`
adds another override the runner has to remember. The runner becomes a
manually-maintained allowlist of "files the image is wrong about".

## Decision

The bench image is rebuilt before every test or pilot launch. The runner
runs `docker build` first, `docker run` second. **No bind-mount overrides
of orchestrator scripts.** The image is the single source of truth for
the orchestrator code path — exactly as P3 (containers-only execution)
already requires.

```
( cd "$WIKI_BENCH_ROOT" && docker build -t kurpatov-wiki-bench:1.17.0-d8-cal . )
docker run --rm ... kurpatov-wiki-bench:1.17.0-d8-cal /opt/forge/run-d8-pilot.py
```

Docker layer caching keeps the rebuild cheap. The Dockerfile is structured
so that long-running steps (`apt-get install`, `pip install
openhands-sdk + sentence-transformers`, e5-base model download) sit
above the COPY layers for the orchestrator scripts. A Python-only edit
invalidates only the COPY + the smoke-test step beneath it; everything
above comes from cache. Measured wall: **~20 s** total, ~5 s of which is
`step8_smoke.py` re-running as a free pre-flight check.

This is an architectural inversion. We were paying ~30 min of
investigation per silent-skew incident to save ~20 s of build time.
Negative trade. Rebuild every time.

## Consequences

- The runner pattern simplifies dramatically:
  ```
  docker build → docker run
  ```
  No `-v $HOST/...:/opt/forge/...` lines. The whole class of "did I
  list this file?" mistakes becomes architecturally impossible.
- Every launch gets a free pre-flight: `step8_smoke.py` runs as part
  of the build (it's a `RUN` after the COPYs), so any orchestrator-side
  regression that breaks the smoke test surfaces in 20 s before any
  expensive LLM round-trip happens. ADR 0010 (test fidelity) gets
  another belt-and-suspenders layer for free.
- Image tag stays stable (`kurpatov-wiki-bench:1.17.0-d8-cal`) but the
  underlying SHA changes. This is fine for our single-host single-
  architect operation — we don't pin SHAs anywhere. If/when forge grows
  multi-host, switch to content-hashed tags.
- Dev iteration cost: one `docker build` per script edit. With cache
  warm: ~3-5 s for a Python-only change, ~20 s including the smoke
  re-run. Negligible against the LLM round-trips that follow.
- For really tight inner loops (debugging a single function),
  `--mount type=bind,src=...,dst=...` is still available as an explicit
  per-invocation override — but it is not the default and not part of
  any committed runner script.

## Anti-patterns rejected

- **"Just bind-mount everything in `/opt/forge/`."** Forces the runner
  to enumerate every script. Forgetting one means silent skew. We
  empirically confirmed this fails on 2026-04-29.
- **"Tag images with content hashes."** Adds a layer of indirection
  for no current benefit; we have one host, one architect, one image
  tag. Revisit if/when those constraints change.
- **"Skip the rebuild when nothing changed."** Docker already does
  this — the cache makes a no-op rebuild ~2 s of overhead. Adding a
  manual `if files_changed` check around `docker build` reinvents the
  cache and is a place for bugs to hide.
- **"Build via Make / a dedicated CI job."** A `make build` target
  exists; it does the same thing. The runner calls `docker build`
  directly to keep "what runs the pilot" and "what builds the image"
  in one script — fewer moving parts.

## Why this is more than a runner tweak

This is the third architectural lesson in a week (ADR 0010 test fidelity,
ADR 0011 NFC/NFD, this) where the failure mode was "two sources of
truth, the wrong one was authoritative". P3 (containers-only execution)
was always the principle; this ADR is the enforcement step. Every
launch goes through the same image-build path, so the architectural
contract "the image is the runtime" cannot be silently violated by a
helpful bind mount.


## Motivation

Per [P7](../../phase-preliminary/architecture-principles.md) — backfit:

- **Driver**: stale container images caused architect-time
  regressions (K1 first run).
- **Goal**: Architect-velocity (no stale-image debugging).
- **Outcome**: lab Make targets `make <lab>` rebuild image
  before every launch.
