# Customer-interview protocol

How to actually run a problem interview. Companion to [the script template](./customer-interview-script-template.md). Per [`product-development-approach.md` § 1](../phase-preliminary/product-development-approach.md).


## Language-primary policy

Per [ADR 0027 § 8](../phase-preliminary/adr/0027-product-development-approach.md): customer-interview scripts and transcripts use the **customer's native language as primary**. For Russian-speaking customer segments (kurpatov-wiki), scripts and transcripts are Russian; for English-speaking segments (future products), English-primary; etc. Schema labels (forge-system-tooling-parsed) stay in their canonical English form. The interviewer (Wiki PM) reads/writes in the customer's language during the interview itself.


## Setup (before the interview)

1. Persona file loaded (per agent activation, per [ADR 0016 § Activation](../phase-preliminary/adr/0016-wiki-customers-as-roles.md)).
2. Persona's [problem-interview script](./problem-interview-script-template.md) authored for this product cycle.
3. Hypothesis under test stated explicitly (one falsifiable claim).
4. Transcript file pre-created at `kurpatov-wiki-wiki/metadata/discovery/interview-transcripts/<persona>/<YYYY-MM-DD>.md` with header (persona, hypothesis, date, interviewer = "Wiki PM agent").

## During the interview — multi-turn dialogue rules

### Listening discipline

- **Wait for the full answer.** No interrupting. No paraphrasing back as a leading restatement.
- **Probe, don't pitch.** "Tell me more about that" / "Why?" / "What did that feel like?" / "What did you do next?" — never "would the wiki help with that?"
- **Ask one question at a time.** Stacked questions ("How did you find it AND what did you think AND would you use X?") force the persona to pick one and lose the others.
- **Embrace silence.** When the persona stops, count three before asking the next question. Often the most informative material comes after a pause.

### Branching rules

The script's questions are a floor, not a ceiling. The interviewer can branch on persona answers:
- If the persona reveals a NEW pain not in the hypothesis → probe that pain (it might be the real story).
- If the persona refutes the hypothesis directly → probe WHY they don't have the pain (existing-alternative? different job?).
- If the persona confirms the hypothesis vaguely ("yeah, that's annoying") → probe for SPECIFICS until either a concrete instance (with timestamp / situation) emerges or the confirmation evaporates.

### Question categories (mix throughout)

| Category | Format | When to use |
|----------|--------|-------------|
| **Past-instance** | "Tell me about the last time you ___" | Anchor real behaviour, not aspiration |
| **Process** | "Walk me through what you did first, then next" | Capture the actual workflow |
| **Forces of Progress** | "What made you switch?" / "What worried you?" | Reveal Push / Pull / Anxieties / Habits |
| **Disambiguation** | "When you say [term], do you mean A or B?" | Catch persona-language that maps to multiple PM concepts |
| **Validation** | "If I understand right, you ___ — is that accurate?" | Use SPARINGLY at end of section to confirm interpretation |

### What NOT to do

- DO NOT pitch the product. The persona must not learn what we plan to build during the interview.
- DO NOT ask "would you..." / "could you..." / "might you...". Future-tense answers are aspirational and unreliable.
- DO NOT confirm-bias-prompt. "So you'd really love a wiki that solved this, right?" — leading question; persona will agree even if false.
- DO NOT chain to solution. "If we built X, would you use it?" is a Solution-interview question, not a Problem-interview question. Keep stages separate.

## Transcript schema

Every interview produces a transcript with:

```markdown
# Problem interview — <persona-slug> × <product> — <YYYY-MM-DD>

- **Persona**: <link to persona file>
- **Product**: <product-slug>
- **Hypothesis under test**: <one falsifiable claim, copied from script>
- **Confirmation/refutation criteria**: <copied from script § 5>
- **Interviewer**: <PM agent or human PM>
- **Duration**: <minutes>

## Dialogue

**PM**: <question>
**<persona-tag>**: <answer>
**PM**: <follow-up>
**<persona-tag>**: <answer>
... (multi-turn)

## Synthesis

- **Hypothesis verdict**: CONFIRMED | REFUTED | AMBIGUOUS | (refined to: <new statement>)
- **Pains surfaced** (in persona's words):
  - <pain 1>
  - <pain 2>
- **Existing alternatives** (what they use today):
  - <alternative 1>
  - <alternative 2>
- **Forces of Progress** (Push / Pull / Anxieties / Habits): <one bullet per force>
- **Surprises** (claims not in hypothesis):
  - <surprise 1>
- **Quotes worth preserving** (verbatim from persona):
  - "..."
  - "..."
- **Follow-up questions for next interview**:
  - <question>
```

The transcript lives in [private repo](https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/) per [ADR 0018 § 7](../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md) (customer assessments are private).

## After the interview

1. Save transcript to private path.
2. Cross-tab with prior interviews of the same persona × product (if any).
3. Update the [discovery summary artifact](./discovery-summary-template.md) — append this interview's verdict to the validated-problem evidence.
4. If hypothesis was REFUTED → revise Plan A on the [Lean Canvas](./lean-canvas-template.md) and document the pivot.
5. If hypothesis was CONFIRMED → add to the validated-problem list; that problem becomes a Solution-stage candidate.
6. If AMBIGUOUS → schedule a follow-up interview with refined questions.

## Stealth-mode (simulated-persona-agent) adaptations

When PM and persona are both LLM agents:
- **PM agent** is spawned with [the script](./problem-interview-script-template.md) + [this protocol](./problem-interview-protocol.md) as tools. PM agent has the hypothesis loaded and the dialogue rules above.
- **Persona agent** is spawned with the [persona file](../phase-b-business-architecture/roles/customers/) + a directive to imitate the persona under interview conditions (NOT the simulated-reading-walk directive of [ADR 0016](../phase-preliminary/adr/0016-wiki-customers-as-roles.md)).
- PM agent and persona agent communicate multi-turn; PM agent saves transcript; persona agent does NOT save anything (it just speaks in-character).
- **Honesty caveat per [approach § 7](../phase-preliminary/product-development-approach.md#7-stealth-mode-caveat)**: simulated-persona-agent transcript is NOT a real-customer transcript. It's useful for hypothesis-formation refinement; NOT for product-market-fit claims.

## Measurable motivation chain

Per [P7](../phase-preliminary/architecture-principles.md):

- **Driver**: forge's customer-walk cycle ([ADR 0016](../phase-preliminary/adr/0016-wiki-customers-as-roles.md)) does not specify how to run a multi-turn interview. Without a protocol, agent-driven interviews drift into reading sessions or pitch demos.
- **Goal**: [Quality](../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95). Disciplined interviews = real validated learning = fewer wrong-direction experiments.
- **Outcome**: this protocol is the canonical interview-execution doc; the script template + this protocol together produce schema-conformant transcripts in private repo.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: prevents interview-drift; gives PM agent a multi-turn discipline; transcripts are cross-product-comparable because of schema.
- **Capability realised**: [Architecture knowledge management](../phase-b-business-architecture/capabilities/forge-level.md) (the meta-capability of keeping forge's discipline internally consistent — these protocols are method, not wiki-product-specific).
- **Function**: Document-problem-interview-protocol.
- **Element**: this file.
