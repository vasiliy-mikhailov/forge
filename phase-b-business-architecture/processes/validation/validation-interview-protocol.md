# Validation-interview protocol

How to run a validation interview. Companion to [the script template](./validation-interview-script-template.md).

## Setup

1. Persona file loaded.
2. Validation-interview script authored.
3. Persona's usage data pulled (sessions, frequency, last use; from product analytics when real, simulated-walk count when stealth).
4. Built MVP available for the persona to reference if needed.
5. Transcript file pre-created at `kurpatov-wiki-wiki/metadata/validation/validation-interview-transcripts/<persona>/<YYYY-MM-DD>.md`.

## During the interview — multi-turn dialogue rules

### Triangulation discipline

Validation interviews are uniquely informative because the persona has BEHAVIOURAL data: actual usage. The interviewer uses this:
- **Anchor probe to last actual use**, not hypothetical: "Tell me about your last use" forces real-instance recall.
- **Compare reported behaviour to logged behaviour** — if persona says "I use it daily" but logs show 2x/week, that's information (forgot? aspirational answer? logging gap?).
- **Don't pitch features** — the persona is the user; the persona knows.

### Listening rules (same as prior protocols)

- One question at a time.
- Open-ended.
- Past-tense / present-tense behaviour > future-tense aspiration.
- Embrace silence.

### Branching rules

- Persona reports satisfaction without behaviour data: probe for specifics until concrete usage instance surfaces.
- Persona reports dissatisfaction with usage continuing: probe for what's keeping them — switching cost? lock-in? sunk-cost? Any of these = weak retention signal.
- Persona reports churn (stopped using): probe WHEN, WHY, WHAT-INSTEAD. Most informative interview type.

## Transcript schema

```markdown
# Validation interview — <persona-slug> × <product> — <YYYY-MM-DD>

- **Persona**: <link>
- **Product**: <product-slug>
- **MVP under validation**: <link to MVP sketch + Phase F experiment>
- **Usage data attached**: sessions=<N>, frequency=<X/week>, last-use=<date>
- **Confirmation/refutation criteria**: <copied from script § 5>
- **Interviewer**: <PM agent or human PM>
- **Duration**: <minutes>

## Dialogue
... (multi-turn)

## Synthesis
- **PMF verdict**: CONFIRMED / REFUTED / PARTIAL
- **Usage pattern**: <description>
- **Retention signal**: STRONG / WEAK / NONE / CHURNED
- **Willingness-to-pay signal** (if probed): <Van Westendorp values OR "deferred — stealth">
- **Features used heavily**: <bullets>
- **Features ignored**: <bullets>
- **Switching from alternative?**: yes / partial / no
- **Quotes worth preserving**: "..."
- **Follow-up questions**: <bullets>
```

Transcripts live in private repo per [ADR 0018 § 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

## After the interview

1. Save transcript private path.
2. Cross-tab with prior validation interviews for this persona × product.
3. Update [validation summary](./validation-summary-template.md) with this verdict.
4. If PMF REFUTED across all personas → pivot back to Discovery (was it the wrong problem?) OR Solution (was it the wrong solution?) OR kill.
5. If PMF CONFIRMED across ≥ 2 early-adopter personas with retention + (in real-customer mode) payment signal → ship at scale; product-market-fit declared.
6. If PARTIAL → refine MVP, re-build, re-validate (one cycle; if still partial after two cycles, persevere with weak signal or kill).

## Stealth-mode adaptations

- Persona-agent re-walks the built wiki (similar to the simulated-reading walk per [ADR 0016](../../../phase-preliminary/adr/0016-wiki-customers-as-roles.md)) — this is the proxy for real usage.
- Validation-interview transcripts based on simulated re-walks tell us about quality-regression vs Discovery / Solution baseline; they do NOT tell us about real PMF.
- Transition from stealth to real-customer validation = a Phase A vision amendment + ADR.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: post-launch validation needs disciplined execution.
- **Goal**: [PTS](../../../phase-a-architecture-vision/goals.md) (KR: pts_share ≥ 0.30).
- **Outcome**: this protocol is the canonical validation-interview-execution doc.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: triangulation discipline; behaviour-anchored validation.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Document-validation-interview-protocol.
- **Element**: this file.
