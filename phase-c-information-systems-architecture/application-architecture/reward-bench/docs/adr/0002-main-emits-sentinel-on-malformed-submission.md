# ADR 0002 — `main()` emits sentinel `AttemptResult` on malformed submission

## Status

Accepted (2026-05-13). Active.

## Context

`reward_bench.frameworks.main.main()` is the bench's composition root.
It runs the agent loop against a live vLLM endpoint, loads the
produced `/workspace/submission.py`, scores it on the canonical 20
seeds, and returns an `AttemptResult`.

Real-system observation from cycle 11: the live model
(`qwen3.6-27b-awq`) occasionally produces a `submission.py` that
does NOT define `class Solver` — e.g. it writes `def solve(state) -> int`
with action indices 0/1/2/3 instead. When the harness tries to
access `module.Solver`, an `AttributeError` is raised.

Three possible behaviours when this happens:

1. **Crash loudly.** `main()` re-raises the `AttributeError`. The
   caller (CI, a campaign driver, a notebook) sees a stack trace.
2. **Emit sentinel.** `main()` catches the error, builds a sentinel
   `AttemptResult(n_games=0, games=(), mean_score=0.0, ...)`, and
   returns. The caller gets a well-formed result back.
3. **Retry.** `main()` re-prompts the model until the submission
   shape is correct, with a retry budget. The result is always a
   real scored attempt or a hard failure when retries are exhausted.

## Decision

`main()` emits a **sentinel `AttemptResult`** on malformed
submissions. The sentinel is:

    AttemptResult(
        mean_score=0.0,
        median_score=0.0,
        std_score=0.0,
        max_max_tile=0,
        n_games=0,                      # <-- discriminator: n_games == 0 means sentinel
        aggregate_walltime_sec=0.0,
        games=(),                       # <-- empty tuple confirms
    )

A caller distinguishes happy vs sad path by checking `n_games == 0`
(or equivalently `len(result.games) == 0`).

Two failure modes are caught and routed to the sentinel:

- `FileNotFoundError` — no `/workspace/submission.py` written.
- `AttributeError` on `module.Solver` — submission written but
  missing the `Solver` class.

Any other exception (failed import, syntax error in the
submission's `.py`, env error, vllm error, etc.) propagates — that's
infrastructure failure, not model output failure.

## Consequences

### Positive

- **Bench survives bad model output.** A campaign that runs 21
  models doesn't abort because model 7 wrote `def solve()`. The
  leaderboard ends up with a 0-row for that model, which is the
  correct comparative signal.
- **Caller logic is uniform.** Callers always get an `AttemptResult`
  and check one field (`n_games`) to discriminate. Versus the
  alternatives, which would mean wrapping every call in try/except.
- **The bench's own tests are honest.** Cycle 11 pinned the
  shape-only contract; cycle 12 pinned the happy-path contract.
  Both contracts coexist because the sentinel is a valid result,
  not an error sneaking through.

### Negative

- **Easy to miss in caller code.** A consumer that reads
  `result.mean_score` without checking `n_games` could conflate a
  malformed-submission run with a model that scored exactly 0.0.
  Mitigation: `n_games == 0` is the documented discriminator and
  the test specs make it explicit.
- **Two definitions of "failure".** Sentinel emission means failure
  is now bench-internal (a row in the report) vs exception-raised
  (a CI failure). Some consumers may want both. Future cycles can
  add an explicit `failure_reason: str | None` field on
  `AttemptResult` if needed.
- **Easy to over-reach.** The sentinel is for *submission shape
  errors* (a model output problem). It is NOT for infrastructure
  errors (vllm down, docker host out of memory, network partition).
  Future contributors must resist the urge to expand the catch
  set; infra errors should crash so they get fixed.

### Reverting

To switch to "crash loudly" (alternative 1), remove the try/except
around `module.Solver` access in `src/reward_bench/frameworks/main.py`
and update the cycle-11 shape-only test to expect the exception.
The cycle-12 happy-path test would be unaffected because it asserts
on the success case.

To switch to "retry" (alternative 3), add a retry loop around the
`run_loop` + `load_submission` step with a budget. The sentinel
fallback would remain for when retries are exhausted.

## Alternatives considered

### A. Crash loudly

Simpler code, but every campaign driver that calls `main()` has to
implement its own try/except. Worse: a bad submission in model 7
of 21 aborts the whole campaign — losing the work done for models
1-6. **Rejected** on operational grounds.

### B. Retry until success

Closer to how a real bench would work in production. **Rejected for
now** because it adds:
- A retry budget (how many?) that requires its own design.
- Coupling between `main()` and the prompt strategy (each retry
  needs a different prompt or it'll fail the same way).
- Latency multiplication when retries fail.

A future cycle MAY add retries on top of the sentinel pattern —
the sentinel becomes the final fallback after N retries fail.

## Implementation pointers

- `src/reward_bench/frameworks/main.py` — the try/except around
  `module.Solver` access, the `_sentinel_attempt_result(reason)`
  helper. Lines ~40-60.
- `tests/reward_bench/frameworks/test_main.py` — the cycle-11
  shape-only test (`...then_attempt_result_emitted`) which
  EXPECTS the sentinel path is valid.
- `tests-spec/reward_bench/frameworks/main/test_spec_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted.md`
  — the test-spec contract that pins both happy + sad paths.

## Cross-references

- [SPEC.md §"Per-attempt directory layout"](../../SPEC.md) — the
  `done` marker is what signals "run finalised" regardless of
  whether the result is a real score or a sentinel.
- [Lab ADR 0001 — Condenser uses the same model as the model under
  bench](0001-condenser-uses-same-model-as-bench.md) — sibling
  decision in the same composition-root cycle.
