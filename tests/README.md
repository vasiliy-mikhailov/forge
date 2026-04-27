# forge — tests model

This directory describes **what forge tests assert and why**, not how.
The bash scripts under `scripts/` and per-lab `tests/smoke.sh` are
*derivations* of these models — hand-written, but every check they
perform must map back to a check documented somewhere here or in a
per-lab `tests/smoke.md`.

If a test script asserts something not documented in a model file, or
a model file declares a signal not asserted by any script, that's a
bug. Fix it by either adding the missing check to the script, or
deleting the obsolete lines from the model.

## Why a separate model?

- **Reviewable in prose.** A bash script tells you *how* to check
  something. Prose tells you *why*, *what could go wrong*, *what the
  check is defending against*. Future-me (and future agents) need
  the why.
- **TDD-friendly.** Changes to behavior flow through the model first,
  then the script, then the code. See "Workflow" below.
- **Forces edge-case hygiene.** Every check has an "Edge cases"
  section with things that have actually bitten us — losing a lesson
  (e.g. the `grep -q | pipefail` SIGPIPE bug) to git-log archaeology
  is how the same mistake gets made twice.

## Workflow (TDD: red → green → refactor)

When you change forge's observable behavior, the order is:

1. **Red — edit the model.** Open the relevant `tests/smoke.md`
   (root or per-lab). Update `Goal` / `Signals` / `Edge cases` so the
   document reflects the new *intended* behavior. Code unchanged;
   model now disagrees with reality.
2. **Red — update the script.** Change the matching assertion in the
   script (`scripts/smoke.sh` if dispatcher behavior, or
   `labs/<lab>/tests/smoke.sh` if a lab check). Run it. It should
   fail — that failure is the "red" in red-green-refactor.
3. **Green — change the code.** Edit the service, compose file,
   Makefile, container, whatever is responsible. Re-run until green.
4. **Refactor.** Tidy prose, dedupe signals, collapse redundant
   checks. Only behaviors *described* in a model are behaviors you
   can rely on being tested.

Commit discipline: it's fine to land all four steps in one commit,
but the message should make clear the model changed first. "just fix
smoke.sh" without touching `tests/` is a code smell.

## Coverage map

After [ADR 0007](../phase-b-business-architecture/adr/0007-labs-restructure-self-contained-caddy.md),
labs are mutex on host :80/:443. Smoke is therefore split: a thin
dispatcher at the root, plus a per-lab smoke under each lab.

| Model file                                       | Covers                                              | Derived script                            |
| ------------------------------------------------ | --------------------------------------------------- | ----------------------------------------- |
| `tests/smoke.md`                                 | The dispatcher contract (find active lab, delegate) | `scripts/smoke.sh`                        |
| `labs/kurpatov-wiki-compiler/tests/smoke.md`     | Compiler lab health (vLLM + caddy + endpoint)       | `labs/kurpatov-wiki-compiler/tests/smoke.sh` |
| `labs/kurpatov-wiki-ingest/tests/smoke.md`       | Ingest lab health (whisper, watchers, pusher)       | `labs/kurpatov-wiki-ingest/tests/smoke.sh`   |
| `labs/rl-2048/tests/smoke.md`                    | rl-2048 lab health (jupyter, mlflow, GPU)           | `labs/rl-2048/tests/smoke.sh`             |
| `labs/kurpatov-wiki-bench/tests/smoke.md`        | Bench preflight (binary, image, gh auth)            | `labs/kurpatov-wiki-bench/tests/smoke.sh` |

Shared assertion helpers: [`scripts/smoke-lib.sh`](../scripts/smoke-lib.sh).
Each per-lab `smoke.sh` `source`s it.

## Conventions for a check

Every check in a model file follows the same three-section shape:

```
### <check-name>

**Goal.** One sentence: what user-visible property we are asserting.

**Signals.** The observable facts that, if all true, prove the goal
holds. Written at a level the test script can verify mechanically.

**Edge cases.** Known ways the check can false-pass or false-fail,
and the disciplines the script must follow to avoid them. Each bullet
should be traceable to a real incident or a real class of failure —
not hypothetical.
```

If a check has no known edge cases, say so explicitly ("None known.").
Don't omit the heading — its absence reads as "I forgot to think
about this."

## Non-goals

- Not a test framework. No runner, no harness, no DSL. Documentation
  that scripts (and humans reading them) are accountable to.
- Not auto-generated or auto-consumed. Nobody parses these files at
  runtime.
- Not exhaustive specification. Documents the checks we actually
  run. Things we don't check today don't belong here — stub TODOs rot.

## See also

- [`phase-g-implementation-governance/operations.md`](../phase-g-implementation-governance/operations.md) → End-to-end smoke.
- [`CLAUDE.md`](../CLAUDE.md) — agent rules.
- [ADR 0007](../phase-b-business-architecture/adr/0007-labs-restructure-self-contained-caddy.md)
  — why smoke is per-lab now.
