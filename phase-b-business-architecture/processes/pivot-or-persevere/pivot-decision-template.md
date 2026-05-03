# Pivot-or-persevere decision — template

The fifth-stage exit artifact: a decision document about what comes next after one Build-Measure-Learn loop closes. Per `phase-b-business-architecture/products/<product>/pivot-or-persevere/<YYYY-MM-DD>-decision.md`.

Per Maurya's *Running Lean* ch. 7: at every cycle close, the team must decide one of three:
- **Persevere** — current Plan A is working; keep iterating.
- **Pivot** — change Plan A in some specific dimension; formalise as ADR.
- **Kill** — abandon the product; learnings preserved.

Without a pre-committed decision template, teams default to "persevere on inertia" (Maurya's "Premature Scaling" failure mode).

## Schema — sections

### 1. Header

```markdown
# Pivot-or-persevere decision — <product> — cycle <N> — <YYYY-MM-DD>

- **Product**: <product-slug>
- **Cycle**: <N>
- **Triggering closure**: <link to Validation summary OR Build-Measure-Learn closure>
- **Decision authored by**: <Wiki PM + Architect>
- **Decision date**: <YYYY-MM-DD>
```

### 2. Closure data summary

What the cycle measured:
- Riskiest assumption(s) tested: <copied from MVP sketch>
- Measurement result: <data>
- Kill criteria evaluation: <met / not met / partial>

### 3. The three options enumerated

#### Option A — Persevere

What "persevere" means for this product:
- Continue current Plan A.
- Next cycle: <which stage; what hypothesis>.
- Confidence basis: <data>.

Risk: persevering past kill-criteria threshold = Premature Scaling (Maurya). Evaluate honestly.

#### Option B — Pivot

The 10 Maurya pivot types (zoom-in / zoom-out / customer-segment / customer-need / platform / business-architecture / value-capture / engine-of-growth / channel / technology). Identify which type:
- **Pivot type**: <one of the 10>
- **What changes on Lean Canvas**: <specific cells>
- **What stays**: <cells unchanged>
- **What past learnings carry forward**: <list>

A pivot MUST land as an ADR amendment to the product's prior strategic ADR (if any) per delete-on-promotion.

#### Option C — Kill

When all evidence says the product cannot reach the goals at the cost we can sustain:
- **Kill rationale**: <one paragraph>
- **Learnings to preserve**: <list>
- **What to delete**: <files / directories per delete-on-promotion>
- **What to keep**: <ADRs documenting the kill; postmortems entry per `postmortems.md`>

### 4. Chosen option + rationale

```markdown
**Chosen**: A | B | C

**Rationale**: <one paragraph citing closure-data evidence>
```

The choice is an **ADR moment**:
- Persevere → no new ADR required (Plan A unchanged).
- Pivot → new ADR or amendment landing the pivot.
- Kill → ADR + postmortems entry.

### 5. What changes on the Lean Canvas

Mark each cell:
- ✓ unchanged
- ✗ deleted (write replacement)
- ⟳ revised (cite reason)

The post-decision Lean Canvas is the artifact of record going forward. Old Lean Canvas deleted per delete-on-promotion (commit history preserves it).

### 6. Hand-off to next cycle

- If Persevere or Pivot: which stage starts next cycle (Discovery / Solution / Build / Validation), and which hypothesis under test.
- If Kill: postmortem entry written; product line files deleted per delete-on-promotion; resource budget freed for other products.

### 7. Measurable motivation chain

Per the per-product-instance pattern.

## Authoring rules

- Length cap: ~800 words. Decision documents are short; rationale is concentrated.
- Chosen option MUST be explicit (A / B / C).
- "Persevere by default" is BANNED per Maurya — must cite evidence for persevere.
- Pivot type MUST be one of the 10 Maurya types — "we'll just keep adjusting" is not a pivot type.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: every Build-Measure-Learn closure produces a pivot/persevere/kill decision; without a template, decisions drift into "persevere by default" (Maurya's most common failure).
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Pre-committed decision discipline + delete-on-promotion = clean pivots; no ghost-Plan-A sticking around.
- **Outcome**: this template is the canonical pivot-or-persevere decision schema.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: forces honest evaluation; prevents inertia-persevere; integrates with delete-on-promotion + ADR discipline.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md) + [Architecture knowledge management](../../capabilities/forge-level.md).
- **Function**: Schema-pivot-or-persevere-decision.
- **Element**: this template file.
