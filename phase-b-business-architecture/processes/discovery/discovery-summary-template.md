# Discovery summary — template

The exit artifact of the Discovery stage. One per product cycle. Per-product instance lives at `phase-b-business-architecture/products/<product>/discovery/discovery-summary.md`.

The Wiki PM authors this artifact at the end of Discovery, **before** entering Solution stage. Contains the validated-problem list, the chosen problem with rationale, and the hand-off to Solution stage.

## Schema — sections in order

### 1. Header

```markdown
# Discovery summary — <product> — cycle <N> — <YYYY-MM-DD>

- **Product**: <product-slug>
- **Cycle**: <N> (Discovery cycles are numbered per product)
- **Lean Canvas at start of cycle**: <link to canvas as it was at the start>
- **Lean Canvas at end of cycle**: <link to current canvas; may differ if a pivot landed>
- **Personas walked**: <list of persona slugs with link to each persona file>
```

### 2. Hypotheses tested

Table format:

```markdown
| Hypothesis | Source (Lean Canvas cell) | Verdict | Evidence (interview transcripts) |
|------------|---------------------------|---------|----------------------------------|
| <falsifiable claim 1> | Problem cell | CONFIRMED | <link to private transcripts> |
| <falsifiable claim 2> | Customer Segments cell | REFUTED | <link to private transcripts> |
| <falsifiable claim 3> | UVP cell | AMBIGUOUS, refined to: <new claim> | <link> |
```

Per [problem-interview-protocol.md § Transcript schema](./problem-interview-protocol.md), each verdict traces to interview evidence in the private repo.

### 3. Validated problems

The list of customer pains that survived hypothesis testing. These become Solution-stage candidates.

Format (per problem):

```markdown
### V-N — <one-line problem statement>

- **Affected segments**: <persona names with links>
- **Frequency**: how many of the N personas voted this problem
- **Severity**: blocking / moderate / mild — by the rule in [customer-problems.md](https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/blob/main/metadata/customer-problems.md) Severity coding
- **Existing alternatives**: what segments use today
- **Evidence**: links to interview transcripts (private repo per [ADR 0018 § 7](../../../phase-preliminary/adr/0018-privacy-boundary-public-vs-private-repos.md))
- **Forces of Progress** (push / pull / anxieties / habits): bullets per force
```

The V-NN ID is local to this discovery summary; cross-references to the Customer-walk-cycle CO-NN observations are explicit when a validated problem maps to one or more existing observations.

### 4. Refuted hypotheses

What we BELIEVED in Plan A that interviews killed. Most useful section in the document — Maurya's discipline says the team that records its falsifications learns fastest.

Format:

```markdown
### R-N — <hypothesis that was refuted>

- **Original Lean Canvas cell**: <cell name and what it said>
- **What interviews revealed instead**: <one paragraph>
- **Pivot landed**: yes / no — if yes, link to ADR
- **Lean Canvas cell after pivot**: <cell name and what it now says>
```

### 5. Opportunity Solution Tree (chosen-problem rationale)

Per [`product-development-approach.md` § 4](../../../phase-preliminary/product-development-approach.md), the OST maps validated problems → solution candidates → experiments. Inline OST sketch (or link to a separate `opportunity-solution-tree.md` for complex trees).

```markdown
Outcome: <named Goal from goals.md, e.g. Quality KR pre_prod_share ≥ 0.95>
├── Opportunity 1 (V-N): <one-line>
│   ├── Solution candidate 1.1: <one-line>
│   └── Solution candidate 1.2: <one-line>
├── Opportunity 2 (V-M): <one-line>
│   └── Solution candidate 2.1: <one-line>
└── Opportunity 3 (V-K): <one-line>
    └── Solution candidate 3.1: <one-line>
```

### 6. Chosen problem (the 1-of-N pick)

The single problem that the team will take into the Solution stage next. With explicit rationale.

```markdown
**Chosen problem**: V-N — <statement>

**Rationale**:
- **Reach**: <how many segments / users affected>
- **Impact**: <expected uplift on the named Goal's KR>
- **Confidence**: <high / medium / low — based on interview evidence count + clarity>
- **Effort**: <ballpark estimate>
- **Why this over the others**: <one-paragraph argument citing the OST>
```

The choice is an **ADR moment** — record it as an ADR if the choice has long-running implications (e.g. choosing Quality-side problems over TTS-side ones changes the product trajectory).

### 7. Hand-off to Solution stage

What the Solution stage starts with:
- The chosen problem.
- The validated personas (Customer Segments cell of Lean Canvas now informed by interviews).
- The existing-alternatives data (interviews surfaced what the segment uses today; Solution must beat that).
- Forces of Progress per persona (anxieties about adopting any new solution).

The Solution stage's first artifact is a Solution-interview script (template queued — to author when forge enters Solution stage).

### 8. Stage-exit measurable motivation chain

The discovery summary itself has a chain (per ADR 0017 universal motivation):

```markdown
### Measurable motivation chain (sample for the per-product instance)

- **Driver**: <product-specific>
- **Goal**: <named Goal> (KR: <KR target>)
- **Outcome**: this discovery summary lands; chosen problem is named; Solution stage is unblocked.
- **Measurement source**: audit-predicate: P26 + P29 + P30.
- **Contribution**: <how this summary advances the cited Goal's KR>
- **Capability realised**: <link>
- **Function**: Discovery-cycle-<N>-summary.
- **Element**: this file.
```

## Authoring rules

- Length cap: ~1500 words. If longer, the cycle covered too much; split into multiple cycles.
- Verdicts MUST be CONFIRMED / REFUTED / AMBIGUOUS — no "interesting" / "worth exploring" weasel-words.
- Refuted-hypothesis section MUST exist even if empty (write "(none — Plan A held in this cycle; queued: revisit on next cycle if confidence is low)").
- Chosen problem section MUST cite a single problem. If the cycle ended without a clear pick, that's a Discovery-stage failure to be recorded explicitly.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: every Discovery cycle needs a single canonical exit artifact; without a template, exit artifacts drift in scope and prevent Solution-stage handoff.
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Template-once / instance-many; clean Discovery → Solution handoff.
- **Outcome**: this template is the canonical Discovery-summary schema; per-product cycle instances cite it.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: produces decision-grade exit artifacts; team enters Solution with one clear problem (not 10 candidate problems).
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Schema-discovery-summary.
- **Element**: this template file.
