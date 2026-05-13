# ADR 0005 — Plateau detection: supervisor asks the bench LLM to judge progress from sweep data

## Status

Accepted (2026-05-13). Active.

## Context

[ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md)
lists `max_no_improve` as a knob: "Reject `finish` if dev_runner
score did not improve in N turns." That's the legacy `_bak`
approach — mechanical, threshold-based.

Mechanical no-improve is brittle:

1. **Noise creates false triggers.** A submission scoring
   3000 → 3050 → 2980 → 3010 is *not* on a plateau; it's
   oscillating around 3000. A `max_no_improve=2` rule would treat
   the third iteration as a non-improvement and over-trigger.
2. **Lucky bumps mask plateaus.** A 3000 → 3000 → 3100 → 3000
   → 3000 sequence looks like progress to a "any improvement
   resets" rule, but the model is actually stuck near 3000.
3. **Per-model variance.** What counts as "no improvement" for
   tier-1 2048 (scores 1k-10k) differs from tier-3 LangGraph
   orchestration (scores in a different unit). Hardcoding
   thresholds is task-coupled.
4. **The judgment is intelligent.** Recognising a plateau in noisy
   sweep data is exactly the kind of pattern recognition LLMs are
   good at — and the model under test ALREADY knows its own
   optimization tendencies.

Per ADR 0001 the bench model is also the condenser model. The same
endpoint, same warm KV cache, can also be the **supervisor**.

## Decision

Replace mechanical `max_no_improve` with a **supervisor** that asks
the bench LLM under test to judge plateau from sweep data.

The supervisor sits between `agent_loop` and `finish`. Every K
turns (or after any dev_runner invocation), the supervisor:

1. Collects the sweep data — a sequence of `(iteration_no,
   dev_runner_mean_score, max_tile, walltime_sec)` tuples for the
   recent N iterations.
2. Posts a short prompt to the bench LLM endpoint (per ADR 0001,
   same model):

       Given this sequence of dev_runner scores, are you on a
       plateau (no meaningful improvement) or still making
       progress? Reply JSON: {"plateau": bool, "reasoning": str,
       "stop_recommended": bool}. Conservative bias — only say
       plateau if you are confident further iterations would not
       improve.

3. Parses the reply. If `stop_recommended == true`, the agent
   loop forces a `finish` (with `note` = the supervisor's
   reasoning).

This makes plateau detection **adaptive per model + per task**.
A smarter model may keep iterating productively when a weaker
model would have stopped; both are judged by their own sense of
progress.

## Consequences

### Positive

- **No threshold tuning.** `max_no_improve` becomes obsolete; one
  fewer knob in `BenchConfig`.
- **Per-model intelligence.** Different models have different
  optimization patterns; each one judges its own.
- **Same-model consistency** with ADRs 0001 and 0004 — one vLLM
  endpoint serves bench, condenser, and supervisor.
- **Honest stop signal.** When the supervisor says "stop", the
  recommended `finish` note carries the supervisor's reasoning into
  the per-attempt artifacts — auditable signal of WHY a run ended.

### Negative

- **Extra inference per check.** One small LLM call every K
  iterations adds cost. Mitigation: K=5 (configurable) so the
  supervisor fires sparingly.
- **Supervisor may be wrong.** A model that's eager to stop will
  bias toward early plateau declarations; a stubborn model will
  bias toward "still making progress" even when it's not. Honest
  trade-off; mechanical detection has the same problem with worse
  failure modes (false stops, missed plateaus).
- **Prompt engineering required.** The supervisor's prompt must
  encourage conservative plateau judgments. Without that, models
  may over-call plateau on the first 2-3 stable iterations.
- **More complexity.** New entity (`SupervisorDecision`), new
  port, new adapter, new hook in `agent_loop`. Worth it given the
  signal quality, but documented complexity.

### Reverting

The supervisor is opt-in via a new `BenchConfig.use_supervisor:
bool` field (default depending on tier). Setting it to `False`
restores the legacy `max_no_improve` behaviour. A future cycle
could combine both: supervisor + fallback to mechanical when the
supervisor errors out.

## Alternatives considered

### A. Keep mechanical `max_no_improve`

Simple, deterministic, no extra inference. **Rejected** because of
the noise/lucky-bump issues described above.

### B. Statistical plateau detection (slope-based)

Compute the slope of the last N scores; if `|slope| < threshold`,
declare plateau. **Rejected** because the threshold is
task-specific — what's "flat" for 2048 may be active progress for
another tier.

### C. LLM self-judgment (this decision)

Adaptive, model-aware. Accepted with the conservative-bias prompt.

### D. Hybrid (supervisor + statistical fallback)

Use the supervisor as primary; fall back to slope-based if the
supervisor errors out or times out. **Deferred** to a future
cycle once the supervisor's failure modes are observed.

## Implementation pointers

- **Entity**: `src/reward_bench/entities/supervisor_decision.py`
  — `SupervisorDecision(plateau: bool, reasoning: str,
  stop_recommended: bool)`. Frozen dataclass.
- **Port**: `src/reward_bench/use_cases/supervisor_port.py` —
  `Protocol` with `assess(sweep_data) -> SupervisorDecision`.
- **Adapter**: `src/reward_bench/adapters/llm_supervisor.py` —
  posts to vLLM (per ADR 0001), parses the JSON response.
  Constructor takes the same `summarise`-style injected callable
  used by `LlmCondenser` so the adapter is testable without a live
  model.
- **agent_loop hook**: every K iterations call
  `supervisor.assess(sweep_data)`; if `stop_recommended`, inject a
  `finish` tool call from outside the model and break the loop
  carrying the supervisor's reasoning as the finish `note`.
- **Sweep data source**: parse `dev_runner` stdout (already
  captured as tool observations in `messages`); pluck
  `(iteration, mean_score, max_tile, walltime_sec)` per call.
- **`BenchConfig` field**: add `supervisor_every_k: int` (e.g.
  default 5).

## Cross-references

- [Lab ADR 0001](0001-condenser-uses-same-model-as-bench.md) —
  same-model rule extends to the supervisor.
- [Lab ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md)
  — supersedes the `max_no_improve` row in the defaults table
  (the supervisor replaces that knob). Update the ADR-0003 row to
  "deprecated; see ADR 0005" when the supervisor lands in code.
- [Lab ADR 0004](0004-condenser-trigger-at-80-percent-of-input-budget.md)
  — supervisor pattern mirrors the condenser pattern (port +
  adapter + injected summarise-style callable).
