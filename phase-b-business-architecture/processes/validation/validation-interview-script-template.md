# Validation-interview script — template

The per-persona script for the Validation stage. Per `phase-b-business-architecture/products/<product>/validation/validation-interview-scripts/<persona>.md`.

Per Maurya: differs from Solution-interview in that the customer has USED the product. Probes are about actual usage, not sketch reactions.

## Schema — sections

### 1. Persona header

- Cross-link to persona file.
- Job statement.
- **Built MVP under validation** — reference to MVP sketch and Phase F experiment.
- **Customer's usage history** — when first used, how often since, last use date.

### 2. Usage probes (5-8 questions)

Past-tense, behaviour-anchored:
- "Walk me through your last use of [the product]."
- "What were you trying to do?"
- "What worked? What didn't?"
- "How does this compare to [existing alternative from Discovery]?"
- "Has anything changed about your job since you started using this?"

### 3. Retention probes (3-5 questions)

- "When was your last use? When do you expect the next one?"
- "Are you still using [existing alternative] alongside?"
- "Have you told anyone about this?" (referrals = retention signal)

### 4. Willingness-to-pay probes (3-5 questions; **deferred in stealth mode**)

- "If this cost X, would you keep using it?"
- "What would you trade off to keep access?"
- "What price feels too cheap (suspicious)? Too expensive (no-go)? Just right?"

Van Westendorp price-sensitivity meter is the canonical structure.

### 5. Confirmation / refutation criteria

- **Confirms PMF** if persona shows: usage-without-prompting AND alternative-displaced AND positive-referral-signal AND payment-acceptance.
- **Refutes PMF** if persona shows: forgot-to-use OR alternative-still-primary OR no-referrals OR payment-rejected.
- **Refines** if persona shows partial signal — surface which feature delivered, which didn't.

## Authoring rules

- Past-tense behaviour primary; future-tense aspiration tertiary.
- One usage instance probed deeply > N usage instances probed shallowly.
- Stealth-mode adaptation: payment-intent probes deferred; usage probes still valid against simulated persona-agent re-reading the built wiki.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: post-launch validation needs structured probes; otherwise PMF claims are anecdote-based.
- **Goal**: [PTS](../../../phase-a-architecture-vision/goals.md) (KR: pts_share ≥ 0.30).
- **Outcome**: this template is the canonical validation-interview script schema.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: structured PMF measurement when forge enters real-customer phase.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Schema-validation-interview-script.
- **Element**: this template file.
