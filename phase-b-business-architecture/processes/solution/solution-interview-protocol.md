# Solution-interview protocol

How to run a solution interview. Companion to [the script template](./solution-interview-script-template.md). Differs from [Problem-interview protocol](../discovery/problem-interview-protocol.md) in three ways: (1) a sketch is presented mid-interview; (2) adoption-intent is probed; (3) sketch revisions land mid-interview if persona surfaces a clear improvement.

## Setup (before the interview)

1. Persona file loaded (per agent activation).
2. Solution-interview script authored for this persona × product × validated problem.
3. Sketch artifact prepared (image / paragraph / mock; minimum-fidelity-to-test-the-hypothesis).
4. Confirmation/refutation criteria explicit (script § 6).
5. Transcript file pre-created at `kurpatov-wiki-wiki/metadata/discovery/solution-interview-transcripts/<persona>/<YYYY-MM-DD>.md`.

## During the interview — multi-turn dialogue rules

### Demo discipline

The sketch is shown ONCE — when the script's § 4 starts. Before that:
- Capture persona's aspirations + mental model + preferred solution shape.
- Do NOT mention product features. Do NOT name the team's solution candidate.

After showing:
- Watch reaction order: first-reaction is most informative; rationalisation comes later and is less reliable.
- Probe missing parts BEFORE wrong parts (missing-part complaints reveal gaps in our model; wrong-part complaints reveal mismatched assumptions).
- DO NOT defend the sketch. The sketch is a hypothesis. If the persona kills it, the sketch dies; the team learns.

### Listening rules (same as Problem-interview)

- One question at a time.
- Open-ended; no leading. "Would you use this?" is BANNED in Maurya's discipline; replace with "Walk me through how you'd integrate this into your week."
- Embrace silence.
- Probe past-tense / present-tense behaviour over future-tense aspiration.

### Branching rules

- If persona refutes the sketch directly → probe WHY (existing-alternative-already-better? doesn't-solve-actual-problem? wrong-segment?). Multiple paths, each producing different next-steps.
- If persona refines the sketch ("this would work IF..."): the conditional is the gold. Capture verbatim. The team's sketch revision lands FROM the persona's words, not from team brainstorm.
- If persona confirms vaguely ("yeah, looks good"): probe SPECIFICS — "When would you first use it? How often? Who else would you tell?" Vague confirmations are unreliable signal.

## Transcript schema

```markdown
# Solution interview — <persona-slug> × <product> — <YYYY-MM-DD>

- **Persona**: <link>
- **Product**: <product-slug>
- **Validated problem under test**: <copied from Discovery summary V-NN>
- **Solution candidate(s) shown**: <list with sketch links>
- **Confirmation/refutation criteria**: <copied from script § 6>
- **Interviewer**: <PM agent or human PM>
- **Duration**: <minutes>

## Pre-sketch dialogue (§ 3 — aspirations)

**PM**: <question>
**<persona-tag>**: <answer>
... (3-5 turns)

## Sketch shown

<inline sketch description or link>

## Post-sketch dialogue (§ 4 — reactions, § 5 — adoption probes)

**PM**: <question>
**<persona-tag>**: <answer>
... (8-13 turns)

## Synthesis

- **Solution-candidate verdicts**:
  - Candidate 1: CONFIRMED | REFUTED | REFINED-TO-X | AMBIGUOUS
  - Candidate 2: ...
- **Aspiration-vs-sketch gap**: <one paragraph — what persona wanted vs what we showed>
- **Adoption signal**: STRONG (would adopt now) / WEAK (might adopt with X) / NONE (won't adopt because Y)
- **Sketch revisions captured** (in persona's words): <bullets>
- **Existing alternatives the sketch must beat**: <bullets>
- **Quotes worth preserving**: "..."
- **Follow-up questions for next interview**: <bullets>
```

Transcripts live in private repo per [ADR 0018 § 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md).

## After the interview

1. Save transcript private path.
2. Cross-tab with prior solution interviews of this persona × product.
3. Update [solution summary](./solution-summary-template.md): append this verdict, revise sketch if persona refined, add adoption-signal data.
4. If sketch was REFUTED across all personas → pivot back to Discovery (revise problem framing) or kill product.
5. If sketch CONFIRMED across ≥ 2 personas with strong adoption signal → MVP sketch authored, Build-Measure-Learn unblocked.
6. If AMBIGUOUS → revise sketch + re-interview (one revision cycle; if still ambiguous after two cycles, persevere with weak signal or kill).

## Stealth-mode adaptations

Same as Problem-interview protocol's stealth-mode section. Simulated-persona-agent solution interviews are useful for sketch-refinement; NOT for product-market-fit claims.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: forge's existing product-development discipline did not specify how to run a solution interview.
- **Goal**: [Quality](../../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95).
- **Outcome**: this protocol is the canonical solution-interview-execution doc.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: prevents pitch-as-interview drift; sketch-revision discipline; adoption-signal capture.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Document-solution-interview-protocol.
- **Element**: this file.
