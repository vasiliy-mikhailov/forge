# ADR 0002 — `main()` emits sentinel `AttemptResult` on malformed submission

## Status

Accepted (2026-05-13). Active.

## Context

`reward_bench.frameworks.main.main()` is the bench's composition root.
It runs the agent loop against a live vLLM endpoint, loads the produced
`/workspace/submission.py`, scores it on the canonical 20 seeds, and
returns an `AttemptResult`.

The live model (`qwen3.6-27b-awq`) occasionally produces a
`submission.py` missing `class Solver` — e.g. `def solve(state) -> int`
with action indices. `module.Solver` then raises `AttributeError`.

Three possible behaviours:

1. **Crash loudly.** Re-raise. Caller sees a stack trace.
2. **Emit sentinel.** Catch, build a sentinel `AttemptResult` with
   `n_games=0`, return.
3. **Retry.** Re-prompt the model with a retry budget.

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

- **Bench survives bad model output.** A 21-model campaign doesn't
  abort because model 7 wrote `def solve()`. A 0-row for that model
  is the correct comparative signal.
- **Caller logic is uniform.** Always get an `AttemptResult`; check
  `n_games` to discriminate. No try/except at every call site.
- **Tests stay honest.** Shape-only and happy-path contracts coexist
  because the sentinel is a valid result, not an error sneaking through.

### Negative

- **Easy to miss in caller code.** Reading `result.mean_score` without
  checking `n_games` conflates malformed-submission with a true 0.0.
  Mitigation: `n_games == 0` is the documented discriminator.
- **Two definitions of "failure".** Sentinel = row in the report;
  exception = CI failure. A future `failure_reason: str | None` field
  could bridge them.
- **Easy to over-reach.** The sentinel is for *submission shape errors*
  only. Infra errors (vllm down, OOM, network) must still crash.

### Reverting

Remove the try/except around `module.Solver` in
`src/reward_bench/frameworks/main.py` and update the shape-only test.
For retry behaviour, wrap `run_loop + load_submission` with a budget;
the sentinel becomes the final fallback.

## Alternatives considered

### A. Crash loudly

Every caller needs try/except. A bad submission in model 7 of 21 aborts
the campaign, losing models 1-6. **Rejected** on operational grounds.

### B. Retry until success

**Rejected for now**: requires a retry-budget design, couples `main()`
to prompt strategy, multiplies latency. A future cycle may layer retries
on top of the sentinel.

## Implementation pointers

- `src/reward_bench/frameworks/main.py` — try/except + `_sentinel_attempt_result(reason)`.
- `tests/reward_bench/frameworks/test_main.py` — shape-only test.
- `tests-spec/reward_bench/frameworks/main/test_spec_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted.md`
  — contract pinning both paths.

## Cross-references

- [SPEC.md §"Per-attempt directory layout"](../../SPEC.md) — the `done`
  marker signals finalisation regardless of score vs sentinel.
- [Lab ADR 0001](0001-condenser-uses-same-model-as-bench.md) — sibling
  composition-root decision.
