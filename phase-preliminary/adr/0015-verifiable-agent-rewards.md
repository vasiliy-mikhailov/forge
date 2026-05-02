# ADR 0015 — Verifiable rewards for agentic behaviour tests

**Phase.** Preliminary (architecture method extension).

**Status.** Accepted.

**Date.** 2026-04-30.

## Context

[ADR 0013](0013-md-as-source-code-tdd.md) established that md
files driving runtime behaviour are source code, and
[agentic behaviour tests](../../tests/README.md) verify the
agent's output against a *behavioural specification* (when X then
Y; Set-expected → Arrange → Act → Assert; verdict
PASS / FAIL / PENDING / STALE).

That model surfaces structural conformance but lets through what
Vasiliy named the **Italian strike** (Italian: *sciopero
italiano*; English: *work-to-rule strike*) failure: the agent
technically complies with every rule the test enforces while
producing work that is qualitatively useless. The industrial-
relations origin of the term is precise — workers on a
work-to-rule strike cannot be fired for breaking rules (they
follow the letter of every rule), but the output is
deliberately bad. An agent passing every PASS/FAIL test while
producing thin work is in the same posture by accident.
Examples we've already seen on this corpus:

- The Wiki PM's `corpus-observations.md` is `WP-01..WP-06` PASS,
  but a reader can still find the result shallow: 5 observations
  per bucket meets the predicate, while 50 well-cited
  observations would be substantively better. The PASS verdict
  doesn't distinguish.
- The Auditor's `audit-2026-04-30.md` is `AU-01..AU-04` PASS, but
  it could have produced 3 findings instead of 20 and still
  passed — the predicate doesn't reward thoroughness.
- A Wiki PM agent that classifies *every* line as Air would pass
  the structural tests on output shape but fail on use.

The risk grows as roles multiply: the more agents we formalise,
the more places "Italian strike" can hide while every test goes
green.

ArchiMate 4 already gives us the modeling language for the fix.
The Motivation domain (§6) ties **Drivers → Goals → Outcomes** and
**Capabilities → realize Outcomes**. Per spec §6.4.2:

> Outcomes are tangible, possibly quantitative, and time-related,
> and can be associated with assessments. Capabilities can be
> designed to achieve such outcomes.

A test that scores an agent's output against the **Outcomes** the
role is supposed to realize gives us the missing dimension.
PASS/FAIL becomes the *floor* (minimum conformance); the score
becomes the *ceiling reach* (how much value was actually
produced).

The methodology is also not new at forge: the
[rl-2048 lab](../../phase-c-information-systems-architecture/application-architecture/rl-2048/)
uses **RLVR (Reinforcement Learning with Verifiable Rewards)** —
score is a deterministic function of the agent's output against
a known-good reward signal. ADR 0015 is the same methodology
applied to *agent role evaluation* instead of policy training.

## Decision

**Every agentic behaviour test case grants a verifiable reward
score, and the reward function is tied to the role's motivation
chain.**

Specifically:

1. **Motivation chain stated in the role md.** Every role file
   under `phase-b-business-architecture/roles/` must state the
   chain it serves, in ArchiMate 4 terms:

   ```
   Driver → Goal → Outcome → Capability → Function → Role
                                                       ↑
                                                  this role
   ```

   A role's tests grant rewards measuring how much each test
   case advances the **Outcome** the role's Function realizes.
   New role files include this chain in a `## Motivation chain`
   section; existing role files are amended on next edit.

2. **Reward function per test case.** Each AAA case in a test md
   gains a `### Reward` section that defines:

   - **Score components** — what is measured. Each component is
     a deterministic function over the real result with a
     defined range.
   - **Aggregate score** — how components combine (sum, weighted
     sum, min/max).
   - **Score range** — the maximum and minimum the case can
     yield (e.g. 0..5).
   - **PASS threshold** — the minimum score for the verdict to
     be PASS. Below threshold = FAIL.
   - **Italian-strike band** — the score range where verdict is
     PASS but score is meaningfully below maximum (e.g. PASS
     threshold ≤ score < 0.8 × max). Surfacing this band is the
     anti-italian-strike signal.
   - **Motivation reference** — which Outcome the score
     measures (cite the role's motivation chain).

3. **Verifiable = mechanical.** Reward functions must be
   computable from the real result without LLM judgement
   (consistent with RLVR). LLM-as-judge is permitted for
   sub-components if the LLM's output is itself constrained to
   a numeric / boolean signal (e.g. "does this prose mention
   Selye? yes/no" → 0/1) — the *aggregation* stays mechanical.

   When a property cannot be made mechanical, the test case
   must say so explicitly (`PENDING (no mechanical reward
   function)`); it does not get a fake numeric score.

4. **Verdicts gain a fourth state.** The verdict ladder
   becomes:

   - **STALE** — spec was wrong; needs re-write.
   - **FAIL** — score < PASS threshold.
   - **PASS-italian-strike** — score ≥ PASS threshold but
     < 0.8 × max. Same downstream effect as PASS (test
     "succeeded"), but the audit treats it as a quality signal.
   - **PASS** — score ≥ 0.8 × max.
   - **PENDING** — case authored but no run.

   Runners report all four states. The italian-strike state is
   the new value this ADR adds.

5. **Score history tracked, not just current.** Each runner
   appends per-case scores to a per-runner JSONL log under
   `scripts/test-runners/.score-history/<runner>.jsonl`. Each row
   carries `{ts, git_commit, runner, test_id, verdict, score,
   score_max, threshold, detail}`. Logging is opt-in via the
   `--log-scores` CLI flag — interactive dev runs do NOT pollute
   history; the architect logs scores at the same cadence as
   audits walk (today ~5 days) and before/after material edits.
   Scores over time make regression visible: a role whose
   corpus-observations.md goes from 0.95 to 0.65 is regressing in
   quality even if PASS verdict holds. The Auditor walks regressions
   under [P21](../../phase-h-architecture-change-management/audit-process.md).

6. **Aggregate per role.** A role's overall score is the
   per-case average (or weighted average if cases have
   declared weights). The Auditor reports each role's aggregate
   score in audit findings (a new INFO finding kind: "role X
   averaged 0.72 — italian-strike band — at this commit").

7. **No auto-tuning.** Reward functions are designed by the
   architect, not auto-discovered. A reward function whose
   score routinely diverges from architect eye-read judgement
   is the function being wrong, not the agent — fix the
   function.

## Consequences

**Positive.**

- *Italian strike becomes visible.* An agent that passes
  structurally while producing thin work scores in the lower
  PASS band; runners surface the score; audits report it. The
  failure mode the user named has a name and a metric.
- *Motivation gets typed traceability.* Each role's tests cite
  the Motivation chain (Driver → Goal → Outcome → Capability →
  Function → Role). A future contributor can read any test and
  know which Phase A goal it serves.
- *Regression detection at the agent layer.* Per-role score
  history makes "the role's outputs got worse" a measurable
  event, not a feeling.
- *Unification with rl-2048.* Forge has one methodology for
  evaluation across very different domains (game-playing
  policy, agent role) — both RLVR-based.

**Negative — accepted.**

- Reward function design is hard. Each case needs a function
  that approximates what the architect would judge as "good
  output." Bad functions reward the wrong thing. Mitigated by
  decision point 7 (no auto-tuning; eye-read judgement is the
  ground truth).
- Score noise. Some legitimate-good outputs will score below
  threshold; some legitimate-bad outputs will score above. The
  italian-strike band is meant to absorb part of this noise; the
  rest is architect call on whether to accept the score or
  revise the function.
- More work per test case. Each case grows by a `### Reward`
  section. For mechanical cases this is a few lines; for
  judgement-heavy cases it may not be doable today and the case
  stays PENDING.
- Score gaming risk. An agent that learns to maximise the
  reward without producing real value is the classic RLVR
  hazard. Mitigated by: reward functions are *designed* to
  reward what we actually want; review of reward functions is
  itself a Phase H concern.

**Out of scope.**

- Auto-tuning reward functions. Architect call only.
- Cross-role aggregate rewards (e.g. "the wiki product line
  scored X this week"). Aggregation is a separate concern;
  this ADR establishes per-case + per-role.
- Online learning loop where the agent's output influences its
  own reward function. Forge does not auto-train its agents
  (that would be a Phase B capability change requiring a
  Preliminary re-open).

## Worked example: AU-05 with a reward function

Before ADR 0015 the case verdict was binary:

> When the Auditor's input contains "operations stack", then it
> produces a P6 finding under verdict FAIL citing the phrase. →
> PASS or FAIL.

After ADR 0015:

```
### Reward

Motivation: realizes the *Outcome* "Architecture inconsistencies
are surfaced before they propagate" — rolls up to the
Architect-velocity Goal (Phase A).

Score components (each 0/1 unless noted):
  - C1. Finding exists in FAIL section          (1 pt)
  - C2. Predicate cell names P6                 (1 pt)
  - C3. Symptom paragraph quotes the phrase     (1 pt)
  - C4. Rule paragraph cites ADR 0014           (1 pt)
  - C5. Proposed fix is concrete                (1 pt)
  - C6. Proposed fix would actually resolve it  (1 pt)

Aggregate: sum (range 0..6).
PASS threshold: 3.
Italian-strike band: 3 ≤ score < 5.
Score = 6: ideal (architect would not have to revise).
```

A run that scores 4: PASS, but PASS-italian-strike — the
predicate finds the violation and proposes a fix, but the fix is
vague. The runner emits this state explicitly.

## Currently realised

- This ADR.
- (Sibling commit) `tests/phase-b-business-architecture/roles/test-auditor.md`
  cases AU-05 through AU-09 gain `### Reward` sections (the
  worked-example pattern above).
- (Sibling commit) `scripts/test-runners/test-auditor-runner.py`
  emits scores alongside PASS/FAIL/SKIP and surfaces the
  italian-strike band.
- (Sibling commit) `phase-b-business-architecture/roles/auditor.md`
  + `wiki-pm.md` gain a `## Motivation chain` section citing the
  Driver → Goal → Outcome → Capability → Function → Role chain.

WP-NN cases and the Wiki PM runner are amended in a follow-up
commit; the change pattern is the same.

## References

- [ADR 0013](0013-md-as-source-code-tdd.md) — md is source code;
  TDD applies. ADR 0015 extends "TDD applies" to "TDD with
  rewards applies."
- [ADR 0014](0014-archimate-across-all-layers.md) — ArchiMate 4
  vocabulary. The Motivation chain referenced in §1 of this
  decision uses the verbs and element types defined there.
- [`../archimate-language.md`](../archimate-language.md) — the
  Motivation domain (§6) with definitions of Driver, Goal,
  Outcome, etc.
- [rl-2048 lab](../../phase-c-information-systems-architecture/application-architecture/rl-2048/)
  — sibling RLVR application. Same methodology, different
  domain (policy training instead of role evaluation).
- ArchiMate 4 Specification §6.4.2 (Outcome) — the typed
  element this ADR makes the test reward measure against.


## Motivation chain

Per [P7](../architecture-principles.md) — backfit:

- **Driver**: agentic-md tests need verifiable rewards (RLVR);
  without them, "test passes" is eye-read judgement.
- **Goal**: Architect-velocity; audit reliability.
- **Outcome**: every test case has a Reward function (P17);
  per-runner JSONL score history (dec 5); per-Role aggregate
  table (dec 6).
- **Measurement source**: audit-predicate: P14 + P22 (every test md has Reward section; per-agentic-md aggregate scores reported)
- **Capability realised**: Architecture knowledge management.
- **Function**: Verifiable-rewards-for-agentic-tests.
