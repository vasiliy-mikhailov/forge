# Solution summary — template

The exit artifact of the Solution stage. One per product cycle. Per `phase-b-business-architecture/products/<product>/solution/solution-summary.md`.

The Wiki PM authors this **before** entering Build-Measure-Learn. Contains: surviving-solution-candidate, MVP scope hand-off, and the ledger of refuted candidates.

## Schema — sections in order

### 1. Header

```markdown
# Solution summary — <product> — cycle <N> — <YYYY-MM-DD>

- **Product**: <product-slug>
- **Cycle**: <N>
- **Discovery summary**: <link to discovery summary; cross-references chosen problem V-NN>
- **Lean Canvas at end of Solution**: <link>
- **Personas interviewed**: <list with links>
```

### 2. Solution candidates tested

| Candidate | Adoption signal | Verdict | Sketch revisions made | Evidence |
|-----------|-----------------|---------|------------------------|----------|
| <candidate 1> | STRONG / WEAK / NONE | CONFIRMED / REFUTED / REFINED-TO-2 | <bullets> | <transcript links, private> |
| <candidate 2> | ... | ... | ... | ... |

### 3. Refuted candidates (lessons)

For each refuted candidate:
- What we believed.
- What interviews revealed instead.
- What this teaches about the problem framing.

Most useful section per Maurya — refutations are validated learning.

### 4. Chosen MVP

Link to MVP sketch artifact at `../mvp-sketches/<chosen-mvp>.md` (per [MVP-sketch template](./mvp-sketch-template.md)).

One-paragraph rationale: why this MVP over the alternatives, citing solution-interview adoption-signal data.

### 5. Hand-off to Build-Measure-Learn

What Build receives:
- The MVP sketch (in/out-of-scope explicit).
- Kill criteria pre-committed.
- Riskiest assumptions to test in build.
- Phase F experiment file path: `phase-f-migration-planning/experiments/<id>.md` (the build manifest).

### 6. Stealth-mode caveat

If solution interviews were against simulated personas: explicit caveat per [approach § 7](../../../phase-preliminary/product-development-approach.md). Adoption-signal data is hypothesis-formation refinement, NOT product-market-fit evidence.

### 7. Measurable motivation chain

Per the per-product-instance pattern (sample heading downgraded so audit walker only finds the file's real chain at end):

```markdown
### Measurable motivation chain (sample for the per-product instance)

- **Driver**: <product-specific>
- **Goal**: <named Goal> (KR: <KR target>)
- **Outcome**: solution summary lands; MVP sketch is named; Build-Measure-Learn unblocked.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: <how this summary advances the cited Goal's KR>
- **Capability realised**: <link>
- **Function**: Solution-cycle-<N>-summary.
- **Element**: this file.
```

## Authoring rules

- Length cap: ~1500 words.
- Verdicts MUST be CONFIRMED / REFUTED / REFINED — no weasel-words.
- Refuted-candidates section MUST exist (write "(none)" if nothing refuted; that's also data).
- Chosen MVP MUST link to a populated MVP sketch (not a placeholder).

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: every Solution cycle needs a single canonical exit artifact; without a template, exit artifacts drift.
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling).
- **Outcome**: this template is the canonical Solution-summary schema.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: clean Solution → Build-Measure-Learn handoff.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Schema-solution-summary.
- **Element**: this template file.
