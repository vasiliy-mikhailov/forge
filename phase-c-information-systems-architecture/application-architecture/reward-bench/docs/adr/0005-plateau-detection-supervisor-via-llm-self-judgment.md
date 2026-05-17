# ADR 0005 — Plateau detection: supervisor asks the bench LLM to judge progress from sweep data

## Status

Accepted (2026-05-13). Active.

## Context

[ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) lists
`max_no_improve` — the legacy mechanical, threshold-based plateau rule.

Mechanical no-improve is brittle:

1. **Noise creates false triggers.** 3000 → 3050 → 2980 → 3010 is
   oscillation, not a plateau.
2. **Lucky bumps mask plateaus.** 3000 → 3000 → 3100 → 3000 → 3000
   passes "any improvement resets" while actually stuck.
3. **Per-model variance.** Thresholds are task-coupled (tier-1 2048
   scores vs tier-3 LangGraph units).
4. **The judgment is intelligent.** Recognising plateaus in noisy data
   is what LLMs are good at — and the model under test knows its own
   optimisation tendencies.

Per ADR 0001 the bench endpoint already serves as condenser. Same
endpoint can serve as **supervisor**.

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

3. Parses the reply. If `stop_recommended == true`, force a `finish`
   with `note` = the supervisor's reasoning.

Plateau detection becomes **adaptive per model + per task**.

## Consequences

### Positive

- **No threshold tuning.** `max_no_improve` becomes obsolete.
- **Per-model intelligence.** Each model judges itself.
- **Same-model consistency** with ADRs 0001 and 0004 — one vLLM
  endpoint serves bench, condenser, supervisor.
- **Honest stop signal.** Supervisor reasoning lands in `finish` note,
  auditable in per-attempt artifacts.

### Negative

- **Extra inference per check.** Mitigation: K=5 default.
- **Supervisor may be wrong.** Eager models stop early; stubborn ones
  miss plateaus. Mechanical detection has the same problem with worse
  failure modes.
- **Prompt engineering required.** Conservative-bias prompt prevents
  over-calling plateau early.
- **More complexity.** New entity, port, adapter, hook in `agent_loop`.

### Reverting

Opt-in via `BenchConfig.use_supervisor: bool`. Setting `False` restores
legacy `max_no_improve`. Future cycle could combine both.

## Alternatives considered

### A. Keep mechanical `max_no_improve`

**Rejected**: noise/lucky-bump issues above.

### B. Statistical plateau detection (slope-based)

**Rejected**: slope threshold is task-specific.

### C. LLM self-judgment (this decision)

Accepted with conservative-bias prompt.

### D. Hybrid (supervisor + statistical fallback)

**Deferred** until supervisor failure modes are observed.

## Implementation pointers

- **Entity**: `src/reward_bench/entities/supervisor_decision.py` —
  `SupervisorDecision(plateau: bool, reasoning: str, stop_recommended: bool)`.
- **Port**: `src/ports/supervisor.py` — `judge(sweep) -> SupervisorDecision`.
  Default `NullSupervisor` at `src/reward_bench/adapters/null_supervisor.py`.
- **Adapter**: `src/reward_bench/adapters/llm_supervisor.py` — posts to
  vLLM, parses JSON. Constructor takes an injected `summarise`-style
  callable for testability.
- **agent_loop hook**: every K iterations call
  `supervisor.assess(sweep_data)`; if `stop_recommended`, inject `finish`.
- **Sweep data source**: parse `dev_runner` stdout from tool observations.
- **`BenchConfig` field**: `supervisor_every_k: int` (default 5).

## Cross-references

- [Lab ADR 0001](0001-condenser-uses-same-model-as-bench.md) — same-model rule.
- [Lab ADR 0003](0003-bench-defaults-500-iters-10-trials-temp-0.7.md) —
  supersedes the `max_no_improve` row.
- [Lab ADR 0004](0004-condenser-trigger-at-80-percent-of-input-budget.md)
  — supervisor pattern mirrors the condenser pattern.
