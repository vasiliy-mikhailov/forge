# Solution-interview script — template

The per-persona interview-question schema for the Solution stage. Per `phase-b-business-architecture/products/<product>/solution/solution-interview-scripts/<persona-slug>.md`.

Per Maurya's *Running Lean* Solution-interview structure: differs from Problem-interview in that it presents a SKETCH and probes for adoption signal.

## What a solution interview is for

To test whether a proposed solution sketch actually solves the validated problem (from Discovery) — and whether the segment would adopt it given existing alternatives. NOT to validate the build (that's Validation stage). NOT to refine the problem (that's Discovery).

## Schema — sections of the per-persona script

### 1. Persona header

- Cross-link to persona file in [`../../roles/customers/`](../../../roles/customers/).
- Job statement (carried over from persona file).
- **Validated problem under solution test** — the problem this script targets, copied from Discovery summary's V-NN.

### 2. Solution candidate(s) being shown

For each candidate:
- One-line description.
- Sketch artifact link (image / paragraph / mock).
- The minimum claim the sketch makes about how it solves the validated problem.

Maximum 2-3 candidates per interview. More than that overwhelms; less than 2 = not testing trade-offs.

### 3. Demo questions (3-5)

Open-ended questions presented BEFORE the sketch:
- "Tell me how you'd want this kind of problem to be solved."
- "What would the ideal version look like to you?"

Capturing aspirations BEFORE showing the sketch surfaces the gap between persona's mental model and our sketch.

### 4. Sketch reaction (5-8 questions)

Show the sketch. Then probe:
- "What's your first reaction?"
- "What's missing?"
- "What's wrong?"
- "What would make you NOT use this?"
- "How does this compare to [existing alternative from Discovery]?"

Persona-language quoting matters most here — capture verbatim.

### 5. Adoption probes (3-5)

Test willingness-to-adopt:
- "If this were available today, would you use it? When? How often?"
- "What would make you switch from [existing alternative]?"
- "What would prevent you from sharing this with [colleague / friend / Лера]?"

Note: Maurya's discipline — past-tense / present-tense behaviour data is more reliable than future-tense aspirational. Interviewer scores responses with this skepticism in mind.

### 6. Confirmation / refutation criteria

For each solution candidate:
- **Confirms** if persona says: <signal>
- **Refutes** if persona says: <signal>
- **Refines to candidate-N** if: <signal>

Without explicit criteria, the interview produces nice quotes but no validated learning.

## Authoring rules

- Show the sketch — don't pitch the product. Sketch is a hypothesis, not a sale.
- One script per persona × product cycle. Solution-stage interviews use the same persona-set as Discovery (sometimes pruned to early-adopters).
- Demo questions FIRST (capture aspiration) → sketch reactions SECOND (capture compare-to-aspiration delta) → adoption probes LAST (capture willingness-to-act).

## Stealth-mode adaptation

When persona is simulated, the sketch is shown to the persona-agent as text + (optional) image-described-in-text. Persona-agent reacts in-character. Same caveat as Problem-interview: simulated reactions ≠ real-customer reactions.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: without a script template, solution interviews drift into product pitches.
- **Goal**: [Quality](../../../phase-a-architecture-vision/goals.md) (KR: pre_prod_share ≥ 0.95). Disciplined solution interviews = validated solutions before Build = fewer pivots after Build.
- **Outcome**: this template is the canonical solution-interview script schema.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: prevents pitch-as-interview drift; produces decision-grade solution validation.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Schema-solution-interview-script.
- **Element**: this template file.
