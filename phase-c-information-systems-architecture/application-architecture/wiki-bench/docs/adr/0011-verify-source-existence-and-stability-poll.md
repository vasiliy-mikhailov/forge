# ADR 0011 — `verify_source` uses existence + stability poll, not sleep-and-retry

## Context

The K1 pilot (`forge:phase-f-migration-planning/experiments/K1-modules-000-001.md`)
hit intermittent verify-source failures: the agent finished a source,
the orchestrator's `verify_source(stem, module_subdir)` ran
`bench_grade.py` against the artifact, and `bench_grade.rglob` returned
no match — even though the artifact landed seconds later.

**Why the race exists.** The orchestrator runs the agent inside a
container. The agent's `file_editor` tool calls `open() / write()`
on the target source.md and returns "Created file at X" to the
agent's observation. The agent then calls `finish()`. The
orchestrator returns from `conv.run()` and forks a subprocess
running `bench_grade.py`, which does `rglob` for the file.

In a clean POSIX world this is fully synchronous — once `close()`
returns, the inode is visible to any subsequent process. But the
OpenHands SDK's `file_editor` appears to signal completion to the
agent's loop **before** the underlying close-and-flush has fully
propagated. The forked subprocess sometimes runs before the file
is visible.

A second related concern: even when the file does appear, naïve
`exists() + size > 0` doesn't prove it's done being written. A
partial write looks "exists, non-empty" but is actually mid-flight.

**First attempt — sleep-and-retry.** The original `verify_source`
ran `bench_grade.py` once, immediately. After K1 SRC 0 raced, we
added a 1-retry-after-2-s loop. After K1 SRC 6 raced past 2 s, we
extended to 5 retries with backoff (~23 s budget). Both versions
were band-aids: sleep-and-pray, not real synchronization. They
also entangled two distinct questions in one loop:
   - "is the artifact on disk?" (a filesystem question)
   - "is the artifact structurally valid?" (a semantic question)

## Decision

`verify_source` runs in three stages, separating the filesystem
question from the semantic question:

1. **Existence poll.** `target.stat()` at 500 ms cadence until
   `size > 0`. Deadline 30 s. If the file never appears, declare
   verify=fail with the diagnostic message *"agent likely did not
   write the file"* — at this point a missing file is a real
   agent bug, not a timing race.
2. **Stability poll.** Once `size > 0`, poll at 500 ms cadence
   until `(size, mtime)` are unchanged across two consecutive
   samples. Catches partial writes (size still growing) and
   rewrites (mtime changing). Same 30 s deadline.
3. **Single-shot grade.** Run `bench_grade.py` **exactly once**
   for structural verdict. By stage 3 we know the artifact is
   durable; the verdict is real, no retry.

Polling is the cheapest robust synchronizer for this layer. The
file is local and small; 500 ms-cadence stat() costs nothing. The
30 s deadline is permissive enough for the slowest observed agent
race in the K1 run.

## Consequences

- **Diagnostic clarity.** A "file did not appear" verdict is now
  distinguishable from a "file is structurally broken" verdict.
  The first means a real agent failure (didn't write the file or
  wrote to the wrong path); the second means a real authoring
  contract violation (wrong shape, missing section, broken
  cross-ref).
- **No more sleep-and-retry on grade.** The earlier band-aid would
  re-run the entire `bench_grade.py` rglob+grade pipeline several
  times to wait out the race. Stage 1's stat poll is much cheaper
  and gives the same wait-for-file-to-appear semantics without the
  IO and parsing overhead.
- **Stability poll catches a class of bug we previously couldn't
  see.** If the agent overwrites source.md mid-grade — for example
  it wrote a draft, called finish, then for some reason wrote
  again — stage 2 detects the mtime change and waits. Earlier
  versions would race the rewrite.
- **Bound is asymmetric.** A real agent failure (file never
  written) costs 30 s before the orchestrator declares fail and
  fail-fasts. A real success costs ~1 s (file appears
  immediately, stable on second sample). This is the right
  trade-off — failures are rare and the 30 s wait gives a clean
  signal; successes are common and the polling overhead is
  negligible.

## Alternatives considered

- **Atomic write+rename in `file_editor`.** Cleanest fix, but
  requires upstream OpenHands SDK change. The agent would write
  to a temp path, call `os.rename(temp, target)` (atomic on
  POSIX); subsequent `rglob` either sees the file complete or not
  at all. Out of scope at our layer until the SDK is patched.
- **Have `finish()` validate the artifact before returning
  success.** The agent's `finish()` callback could read back the
  file it claims to have written. Also requires SDK or
  prompt-level change; harder to enforce.
- **Inotify watcher.** Kernel API for edge-triggered file-system
  events. Correct but heavy; overkill for a local file in a
  short-lived loop. Polling at 500 ms is comparable in latency
  with much less complexity.
- **Just sleep longer.** What we had been doing. Doesn't scale —
  longer sleep means longer wait on every successful source, not
  just races. Polling has the same worst-case latency but a much
  better best-case.

## Cross-references

- The pattern that triggered this: K1 SRC 0, SRC 1, SRC 6
  (verify-source races) — see
  [`../../../../../phase-f-migration-planning/experiments/K1-modules-000-001.md`](../../../../../phase-f-migration-planning/experiments/K1-modules-000-001.md)
  closure notes when K1 finishes.
- Implementation:
  [`../../orchestrator/run-d8-pilot.py`](../../orchestrator/run-d8-pilot.py)
  function `verify_source`.
- The earlier band-aid commits: `891494c` (initial 1-retry+2s),
  `42a3147` (extended retry budget), `0da7d4d` (replaced with
  two-stage poll).
- Phase D services this affects:
  [`../../../../../phase-d-technology-architecture/services/agent-orchestration.md`](../../../../../phase-d-technology-architecture/services/agent-orchestration.md)
  (wiki-bench's orchestration of agent + per-source verify).
