# Validation summary — template

The exit artifact of the Validation stage. Per `phase-b-business-architecture/products/<product>/validation/validation-summary.md`.

## Schema — sections

### 1. Header

```markdown
# Validation summary — <product> — cycle <N> — <YYYY-MM-DD>

- **Product**: <product-slug>
- **MVP under validation**: <link to MVP sketch + Phase F experiment>
- **Personas validated**: <list>
- **Real-customer or stealth?**: <real / stealth — explicit>
```

### 2. PMF verdicts per persona

| Persona | Usage frequency | Retention signal | Willingness-to-pay | Verdict |
|---------|-----------------|-------------------|---------------------|---------|
| <persona 1> | <X/week> | STRONG / WEAK / NONE / CHURNED | <signal or "deferred"> | CONFIRMED / PARTIAL / REFUTED |
| ... | | | | |

### 3. Validated feature set

Features that early-adopter persona(s) actually used + retained on:
- <feature 1>: <usage frequency> + <retention> + <referral count>
- ...

Features ignored (consider deprecation):
- <feature 2>: <ignored signal>

Features wanted but missing (consider next-cycle inclusion):
- <feature 3>

### 4. Aggregate PMF verdict

CONFIRMED / PARTIAL / REFUTED + 2-paragraph rationale citing per-persona evidence.

### 5. Hand-off to Pivot-or-persevere

What pivot-or-persevere receives:
- The PMF verdict.
- The kill criteria from MVP sketch — was the threshold crossed?
- Validated feature set vs sketch in-scope — what landed, what didn't.
- Cost-data update — actual build cost vs MVP estimate; feeds [EB Goal](../../../phase-a-architecture-vision/goals.md) unit_economics.

### 6. Stealth-mode caveat

If validation was against simulated personas: explicit per [approach § 7](../../../phase-preliminary/product-development-approach.md). PMF-claim reliability is hypothesis-formation refinement, NOT product-market-fit declaration.

### 7. Measurable motivation chain (sample for the per-product instance)

(Same structure as Discovery / Solution per-product instance chains — author with named Goal + Contribution + Element.)

## Authoring rules

- Length cap: ~1500 words.
- PMF verdict MUST be CONFIRMED / PARTIAL / REFUTED — no "promising" / "interesting" / "TBD".
- Stealth-mode caveat is mandatory if applicable.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: every Validation cycle needs a single canonical exit artifact.
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling).
- **Outcome**: this template is the canonical Validation-summary schema.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: clean Validation → Pivot-or-persevere handoff.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Schema-validation-summary.
- **Element**: this template file.
