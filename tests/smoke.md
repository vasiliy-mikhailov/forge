# Smoke test — root dispatcher

After the labs/ refactor (ADR 0007), labs are mutex on host ports
80/443: only one lab's caddy can be running at a time. Smoke is
therefore **per-lab** — there is no longer a single forge-wide smoke
that asserts the whole stack at once.

This file is the source of truth for the **dispatcher** in
[`scripts/smoke.sh`](../scripts/smoke.sh), not for individual checks.
Per-lab smoke contracts live alongside each lab:

- [`phase-c-information-systems-architecture/application-architecture/wiki-compiler/tests/smoke.md`](../labs/wiki-compiler/tests/smoke.md)
- [`phase-c-information-systems-architecture/application-architecture/wiki-ingest/tests/smoke.md`](../labs/wiki-ingest/tests/smoke.md)
- [`phase-c-information-systems-architecture/application-architecture/rl-2048/tests/smoke.md`](../labs/rl-2048/tests/smoke.md)
- [`phase-c-information-systems-architecture/application-architecture/wiki-bench/tests/smoke.md`](../labs/wiki-bench/tests/smoke.md)

Shared helpers (pretty-print, container/GPU/HTTP/log assertions) are in
[`scripts/smoke-lib.sh`](../scripts/smoke-lib.sh) — every per-lab
smoke `source`s this one library.

## Dispatcher contract

### Goal

`make smoke` (or `./scripts/smoke.sh` directly) figures out which
service-lab is currently running and delegates to that lab's
`tests/smoke.sh`, passing through args and exit code.

### Signals

The dispatcher detects which lab is active by looking at running
caddy containers. Exactly **one** of the following must be in
`docker ps --format '{{.Names}}'`:

| caddy container                    | active lab                       |
| ---------------------------------- | -------------------------------- |
| `kurpatov-wiki-compiler-caddy`     | `phase-c-information-systems-architecture/application-architecture/wiki-compiler/`   |
| `kurpatov-wiki-ingest-caddy`       | `phase-c-information-systems-architecture/application-architecture/wiki-ingest/`     |
| `rl-2048-caddy`                    | `phase-c-information-systems-architecture/application-architecture/rl-2048/`                  |

If exactly one matches, the dispatcher `exec`s that lab's
`tests/smoke.sh`. Bench is a client of compiler (no caddy of its own);
its smoke is invoked separately via
`make -C phase-c-information-systems-architecture/application-architecture/wiki-bench smoke`.

### Exit codes

| code | meaning                                                              |
| ---- | -------------------------------------------------------------------- |
| 0    | Active lab's smoke passed.                                           |
| 1    | Active lab's smoke had failures, OR multiple labs' caddies are up.   |
| 2    | No service-lab caddy is running (no lab is active).                  |

### Edge cases

- **Multiple caddies up**. Indicates a stale container that didn't
  exit cleanly when the previous lab was brought down. The dispatcher
  treats this as a *broken invariant*, not a "let me pick one" — it
  prints all active caddies and exits 1. Recovery: `make stop-all`,
  then bring the desired lab up.
- **Lab caddy up but container in a fast restart loop**. Race
  condition: the caddy might appear "Up" briefly between restarts.
  The dispatcher does not retry; the per-lab smoke catches the loop
  on its container-up assertion (status doesn't start with `Up`).
- **Bench co-running with compiler**. Bench has no caddy, so the
  dispatcher routes to the compiler lab. Bench's own smoke
  (`make -C phase-c-information-systems-architecture/application-architecture/wiki-bench smoke`) is a separate command,
  not a fallthrough — the user explicitly asks for it.

## Why per-lab, not whole-forge

Before ADR 0007, a single root smoke walked all subsystems
(`caddy`, `mlflow`, `jupyter-rl-2048`, `jupyter-kurpatov-wiki`,
`kurpatov-ingest`, `kurpatov-wiki-raw-pusher`) on the assumption all
were up at once. After labs/ refactor, that assumption is *wrong*:
labs share host ports and (sometimes) the GPU. A whole-forge smoke
under that constraint has to skip-or-fail-or-conditionally-check
based on which lab happens to be up — which is exactly the dispatch
logic, just smeared across one giant script. Decomposing makes the
contract per-lab obvious and removes "skip-if-down" branches from
the per-section assertions.

## See also

- [`tests/README.md`](README.md) — TDD workflow + check conventions.
- [`phase-g-implementation-governance/operations.md`](../phase-g-implementation-governance/operations.md) — runbook for `make smoke`.
- ADR [`0007-labs-restructure-self-contained-caddy.md`](../phase-b-business-architecture/adr/0007-labs-restructure-self-contained-caddy.md)
  — why labs are mutex on :80/:443.
