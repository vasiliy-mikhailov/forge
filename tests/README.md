# forge — test model

This directory is the **source of truth** for what forge's automated
tests assert and why. Test scripts under `scripts/` (e.g.
`scripts/smoke.sh`) are *derivations* of this model — hand-written,
but every check they perform must map back to a check documented
here.

If a test script asserts something that isn't in a model file, or a
model file declares a signal that isn't asserted by any script, that's
a bug. Fix it by either adding the missing check to the script, or by
deleting the now-obsolete lines from the model.

## Why a separate model?

- **Reviewable in prose.** A bash script tells you *how* to check
  something. Prose tells you *why*, *what could go wrong*, and *what
  the check is defending against*. Future-me (and future agents) need
  the why.
- **TDD-friendly.** Changes to behavior flow through the model first,
  then the script, then the code. See "Workflow" below.
- **Forces edge-case hygiene.** Every check has a dedicated "Edge
  cases" section listing things that have actually bitten us. Losing
  a lesson (e.g. the `grep -q | pipefail` SIGPIPE bug) to git-log
  archaeology is how the same mistake gets made twice.

## Workflow (TDD: red → green → refactor)

When you change forge's observable behavior, the order is:

1. **Red — edit the model.** Open the relevant file under `tests/`.
   Add or change `Goal`, `Signals`, or `Edge cases` so the document
   reflects the new *intended* behavior. The code has not changed
   yet; the model now disagrees with reality.
2. **Red — update the script.** Change the matching assertion in
   `scripts/smoke.sh` (or whatever test embodies that model section)
   so it enforces the new signals. Run the script. It should fail —
   that failure is the "red" in red-green-refactor.
3. **Green — change the code.** Edit the service, compose file,
   Makefile, container, whatever is actually responsible for the
   behavior. Re-run the script until it passes.
4. **Refactor.** Tidy the prose, de-dup signals, collapse redundant
   checks. Only behaviors that are *described* in the model are
   behaviors you can rely on being tested.

Commit discipline: it's fine to land all four steps in one commit,
but the commit message should make clear that the model changed
first. "just fix smoke.sh" without touching `tests/` is a code smell.

## Coverage map

| Model file            | What it covers                             | Derived script(s)      |
| --------------------- | ------------------------------------------ | ---------------------- |
| `tests/smoke.md`      | `make smoke` / `scripts/smoke.sh` — every  | `scripts/smoke.sh`     |
|                       | check that must pass on a healthy stack    |                        |

(Future model files land here as new areas grow tests — e.g.
`tests/pipeline.md` for a full drop-video → raw.json → GitHub commit
e2e, `tests/disaster-recovery.md` for the rebuild-from-clone drill.)

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

If a check has no known edge cases, say so explicitly ("None
known."). Don't omit the heading — its absence reads as "I forgot to
think about this," which is exactly what we're trying to prevent.

## Non-goals

- This directory is **not** a test framework. It has no runner, no
  harness, no DSL. It's documentation that a script (or a human
  reading the script) is accountable to.
- The model is **not** auto-generated or auto-consumed. Nobody parses
  these files at runtime. An agent reading the model writes/updates
  the bash by hand.
- The model is **not** exhaustive specification. It documents the
  checks we actually run. Things we don't check today don't belong
  here — stub sections with "TODO" rot.

## See also

- [`docs/operations.md` → End-to-end smoke test](../docs/operations.md)
  — user-facing runbook for `make smoke`.
- [`CLAUDE.md`](../CLAUDE.md) — general agent rules for this repo.
