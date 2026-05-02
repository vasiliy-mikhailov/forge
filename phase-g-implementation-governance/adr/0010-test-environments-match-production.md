# ADR 0010 — Test environments must match production as closely as possible

## Status
Accepted (2026-04-29).

## Context

P5 (`forge:phase-preliminary/architecture-principles.md` —
metric-driven action / "prefer the cheap experiment") was applied
correctly today: faced with a 4-hour K1 hot-patch loop on
`verify_source`, the response was to write synth tests instead of
re-running 25-min production pilots.

But the synth tests — `wiki-bench/tests/synthetic/test_verify_source.py`
tests 1-7 — all *passed*, including test 7 which uses the **exact
Cyrillic + №2 + curly «» path from the K1 SRC 7 failure**. The
production `verify_source` poll, run inside the K1 container against
the same path, **failed** despite the file existing on disk before
the poll started.

The synth tests were lying. They didn't validate what production
actually does because they didn't mirror production's relevant
semantics. Specifically:

- Synth tests wrote the file via `Path.write_text(...)` — direct
  open / write / close in the orchestrator's own Python process.
- Production K1 has the agent's OpenHands SDK `file_editor` tool
  write the file — its own `editor.py` write_file path with
  encoding handling + history caching + diff utilities. Different
  syscall sequence, possibly different process, possibly different
  flush behaviour, possibly different mount-cache propagation
  inside the container.

Because the synth tests didn't reproduce production's *write path*,
they couldn't reproduce the bug. They gave a false-green signal.
A real failure mode that production hits routinely was invisible
to the test harness.

## Decision

**Test environments must match production environments as closely
as possible**, especially in the dimensions that the test is
designed to assert against.

For each new synth/unit test, before declaring it sufficient,
walk through the production call path and check each layer:

1. **Same process / process boundary?** If production runs the
   logic inside a Docker container, the test should too (or
   document why the host-process equivalent is acceptable).
2. **Same write/read mechanism?** If production writes via the
   agent's `file_editor`, a test that uses `Path.write_text`
   doesn't validate the write. Either drive the agent in the
   test, or fake-but-faithful — replicate the syscall sequence.
3. **Same filesystem / mount stack?** If production uses a Docker
   bind mount, a host-only test bypasses any bind-mount cache
   semantics.
4. **Same Python interpreter version + environment?** If the
   production container has Python 3.12 and a specific OpenHands
   SDK version, the test should use the same. Differences in
   pathlib / locale / fs handling matter.
5. **Same locale / encoding?** Cyrillic + Unicode-special-char
   filenames behave differently across locales. Pin LC_ALL.
6. **Same write timing?** A test that puts the file there *before*
   calling the function under test misses races that production
   hits when the file is being written in parallel.

The cheapest test that passes all these "is it actually like
production?" checks beats an exhaustive test that fails any of
them. **A passing test that doesn't replicate the production
path is worse than no test** — it gives a false-confidence
signal.

## Consequences

- **Bench's `tests/synthetic/`** must be re-evaluated against this
  rule. The current `test_verify_source.py` tests 1-7 do not
  drive the agent's `file_editor`; they only validate
  `verify_source` against direct-host writes. They prove the
  function's logic is correct under one input distribution
  (host-write); they do *not* prove correctness under the
  production input distribution (agent-write inside container).
  Either upgrade them to drive the agent (heavier; needs vLLM
  or a mock LLM) or downgrade their interpretation: they are
  unit tests of `verify_source`, not integration tests of the
  orchestrator's per-source loop.
- **New synth tests must pick a fidelity level explicitly** and
  state which production aspects they validate vs. abstract.
  An honest test header: *"this test validates `verify_source`'s
  poll logic against direct-host file writes; it does NOT
  validate behaviour against the agent's `file_editor` write
  path."*
- **Future K1-style failures** are now expected to surface aspects
  the unit-level synth doesn't cover. The architectural answer is
  *integration tests* that run the orchestrator end-to-end against
  a small synth fixture (1-2 sources) inside the same container
  the production pilot uses, with a real or mocked LLM. That's the
  next level above unit synths and should land before the next
  large pilot. (`R-D-test-fidelity` will be a Phase D requirement
  added to the catalog.)

## Anti-patterns explicitly rejected

- **"It's a unit test, fidelity doesn't matter."** It does — if
  you write a unit test for a function whose production
  behaviour is filesystem-mediated, the test that doesn't go
  through the same filesystem is a different unit, not the same
  function.
- **"Run it on host because it's faster."** Speed is bought with
  loss of signal. Per P5's sub-rule, the cheap path is the right
  path *only when it gives the same signal*. Faster + wrong
  signal is worse than slower + correct signal.
- **"Add more retries until it works."** That's the K1 hot-patch
  loop. P5 explicitly rejects iteration on guesses.

## How to apply

When writing a synth test, fill in this header before the first
`def test_*`:

```
# Production call path for the unit under test:
#   <stack from real entry-point down to the function>
# Test fidelity: <what aspects this test reproduces; what it abstracts>
# Skipped on host: <list any aspects that need a container / SDK / vLLM>
```

The header forces the author to articulate the gap between test
and production. If the gap is too big, the test isn't worth the
ink.

## Cross-references

- The principle this realises: P5 (metric-driven action) in
  [`../../phase-preliminary/architecture-principles.md`](../../phase-preliminary/architecture-principles.md).
  Test fidelity is a corollary: the cheap experiment must give
  the same signal, otherwise it's not actually cheap (false
  greens cost more than the time saved).
- The ADR this complements:
  [`../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0011-verify-source-existence-and-stability-poll.md`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/docs/adr/0011-verify-source-existence-and-stability-poll.md)
  — `verify_source`'s poll mechanism. The unit-level tests in
  bench's `tests/synthetic/test_verify_source.py` validate the
  poll's *logic*; this ADR explains why those tests didn't catch
  the K1 production failure.
- The lesson date: 2026-04-29, K1 fresh-start run; SRC 0 + SRC 1
  both verify-failed inside the running container despite the
  source.md files existing on disk before the poll started, with
  the poll's stat() still reporting "did not appear within 90s".
- New requirement opened by this ADR: `R-D-test-fidelity`
  (integration tests inside the bench container that exercise
  the agent → file_editor → verify_source path end-to-end).
  Tracked in
  [`../../phase-requirements-management/catalog.md`](../../phase-requirements-management/catalog.md).


## Motivation

Per [P7](../../phase-preliminary/architecture-principles.md) — backfit:

- **Driver**: K1 silent-skip bug surfaced because synthetic
  tests didn't match production filesystem semantics
  (NFC/NFD).
- **Goal**: Architect-velocity (synth tests catch real bugs).
- **Outcome**: test environments declare production-fidelity
  axes (filesystem, locale, Python version, write timing).
