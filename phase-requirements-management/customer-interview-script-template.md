# Customer-interview script — template

The per-persona interview-question schema for the Discovery stage of forge's [product-development approach](../phase-preliminary/product-development-approach.md). One script per persona × product. Per-product instances live at `phase-b-business-architecture/products/<product>/discovery/problem-interview-scripts/<persona-slug>.md`.

Per Maurya's *Running Lean* Problem-interview structure + Bob Moesta's [Jobs-to-be-Done](../phase-preliminary/product-development-approach.md#3-complement--jobs-to-be-done-for-persona-depth) interview discipline + Teresa Torres's open-ended-question rule.

## What a problem interview is for

To validate (or refute) the assumption that a particular customer segment has a particular pain. NOT to pitch the product. NOT to validate a solution. Solution interviews come later.

The interviewer (PM) tries to be wrong. The interview is successful if the customer reveals the actual job, the actual workarounds, the actual frustrations — even if those don't match the team's Plan A.

## Schema — sections of the per-persona script

Authored as 6 sections in this order. Total artifact ~600-1000 words.

### 1. Persona header

Cross-link to the persona file in [`../phase-b-business-architecture/roles/customers/`](../phase-b-business-architecture/roles/customers/). State the **Job statement** explicitly (per JTBD § 3 of the approach). State the **early-adopter signal** for this persona (what would tell us this person is desperate enough to be an early adopter).

### 2. Hypothesis under test

The team's Plan A claim about this persona's pain. Stated as a falsifiable proposition. Examples:
- "Marina cannot use the wiki for her chapter because primary-source citations are missing 90 % of the time."
- "Антон-PM stops reading after 12 minutes if there's no TL;DR within the first 2 minutes."

The hypothesis MUST be specific enough that an interview answer can confirm or refute it.

### 3. Opening (2-3 questions)

Open-ended questions to learn the persona's context BEFORE introducing any product framing. Goal: surface the actual job, push, anxieties, habits.

Maurya / JTBD discipline:
- Open-ended only. NO "would you...", "if we built X, would you...". Those are leading.
- Past-tense + present-tense behaviour. NO future-tense ("would you" / "could you" / "might you").
- "Tell me about the last time you ___" anchors a real instance.

Examples (template):
- "Tell me about the last time you tried to [achieve persona's job]."
- "Walk me through what you did first, then next, then next."
- "What was frustrating about it?"

### 4. Probe (5-8 questions)

Open-ended, drill into the hypothesis under test. Format borrows Moesta's "Forces of Progress":

- **Push** ("What made you start looking for a different way to do this?")
- **Pull** ("What made [the alternative they currently use] attractive?")
- **Anxieties** ("What worried you about switching?")
- **Habits** ("What kept you using [old way]?")

Plus targeted probes for the specific hypothesis.

### 5. Confirmation / refutation questions (2-3)

Designed to disambiguate. The interviewer should know in advance what answer means CONFIRMED vs REFUTED for the hypothesis.

Format:
```
**Question**: <text>
**Confirms hypothesis if persona says**: <signal>
**Refutes hypothesis if persona says**: <signal>
**Ambiguous if persona says**: <signal>
```

This section is the **decision-making engine** of the interview. Without it, the interview produces nice notes but no validated learning.

### 6. Closing (1-2 questions)

Open-ended close. Capture introducible referrals or further-context offers:
- "Who else faces this problem?"
- "What did I not ask that you wish I had?"

## Authoring rules

- One script per persona × product. Same persona for a different product = a different script (the Job statement may differ).
- Hypotheses ARE per-product. Don't author cross-product scripts; the cross-product synthesis happens in the discovery summary.
- All questions open-ended (no Yes/No). One leading question = the script needs revision.
- Total time budget: ~30 min real interview, ~15 min simulated-persona-agent interview. Script questions chosen to fit.
- The script is a **floor, not a ceiling** — the protocol allows follow-up probes the script doesn't list (per [protocol document](./problem-interview-protocol.md)).

## Stealth-mode adaptation

When the "customer" is a simulated persona-agent (forge today):
- The script is loaded as the user-facing prompt for the agent.
- The agent imitates the persona per its [persona file](../phase-b-business-architecture/roles/customers/).
- The PM agent runs the interview multi-turn, branching on persona-agent responses per the protocol.
- Transcripts are saved to private repo per [ADR 0018 § 7](../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).
- Honesty caveat: simulated persona-agent interview is NOT the same as a real-customer interview. It's useful for hypothesis-formation refinement, NOT for product-market-fit claims.

## Measurable motivation chain

Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: forge's existing customer-walk cycle ([ADR 0016](../phase-preliminary/adr/0016-wiki-customers-as-roles.md)) does not author per-persona problem-interview scripts. Without a script, agent-driven "interviews" devolve into reading sessions; PM hypotheses go un-tested.
- **Goal**: [Quality](../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95). Validated problems = fewer wrong-direction experiments.
- **Outcome**: this template is the canonical schema for per-persona problem-interview scripts; per-product instances cite it.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: gives the Wiki PM a script template to fill in instead of authoring schema each cycle; reduces per-cycle invention; future predicate (queued: P32 — "every problem interview script cites this template's section structure") makes drift auditable.
- **Capability realised**: [Architecture knowledge management](../phase-b-business-architecture/capabilities/forge-level.md) (the meta-capability of keeping forge's discipline internally consistent — these protocols are method, not wiki-product-specific).
- **Function**: Schema-problem-interview-script.
- **Element**: this template file.
