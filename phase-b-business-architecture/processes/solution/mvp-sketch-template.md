# MVP sketch — template

The minimum-viable-product scope artifact. Per `phase-b-business-architecture/products/<product>/solution/mvp-sketches/<sketch-name>.md`.

Per Maurya: an MVP is the smallest thing that can deliver the core value proposition AND test the riskiest remaining assumption. Less is more.

## Schema — sections in order

### 1. Header

- **Product**: <product-slug>
- **Cycle**: <discovery-cycle-N> → <solution-cycle-N>
- **Validated problem**: <V-NN from Discovery summary>
- **Chosen solution candidate**: <from solution interviews — the candidate that survived>
- **Sketch authored**: <YYYY-MM-DD>
- **Author**: <Wiki PM or product owner>

### 2. Core value proposition

One sentence. Maurya format: *"\[Single result customer wants\] without \[their existing pain point\]."* (Already on the Lean Canvas; copy here for self-containment.)

### 3. The smallest thing we'd build

In-scope (the MVP). Aim for ≤ 5 features:
- <feature 1>: solves <which part of the validated problem>
- <feature 2>: solves <which part>
- <feature 3>: ...

If 5 features feels too few, the team is over-building. Maurya: the MVP exists to learn, not to satisfy.

### 4. Out-of-scope

Explicit list of things the team is NOT building in this MVP:
- <thing 1>: deferred because <rationale> (e.g. "no early-adopter persona requested it"; "blocked by upstream architecture decision")
- <thing 2>: ...

The out-of-scope list is THE most important section. Maurya: "deciding what to leave out is the design discipline."

### 5. Riskiest remaining assumption(s)

The MVP must test the riskiest hypothesis that survived Discovery + Solution interviews. List 1-3:
- <assumption 1>: tested by <which MVP feature>; success = <measurable signal>
- <assumption 2>: ...

If the MVP doesn't test a riskiest-assumption, it's a vanity-build. Revise.

### 6. Kill criteria

Pre-committed: under what observed result will the team kill this MVP?
- After <N weeks / N users / N usage events>, if <metric> < <threshold>, kill.
- Pivot vs persevere decision lives in the [pivot-or-persevere](../pivot-or-persevere/pivot-decision-template.md) artifact post-build.

Pre-committing kill-criteria prevents motivated-reasoning post-build ("but the metric was just slightly off").

### 7. Build cost estimate

- Engineering cost: <ballpark hours / weeks>
- GPU compute cost: <ballpark>
- Architect-time-at-shadow-rate cost: <ballpark>

Cost feeds [EB Goal](../../../phase-a-architecture-vision/goals.md) (KR: unit_economics ≥ 1.0). MVP that costs more than the validated value proposition is delivered = no-go.

### 8. Phase F experiment hand-off

The MVP becomes a Phase F experiment when build starts. The experiment file is created at `phase-f-migration-planning/experiments/<id>.md` with:
- Spec section ← this MVP sketch
- Build-Measure-Learn section ← per [Phase F template](../../../phase-f-migration-planning/experiments/) and [build-measure-learn README](../build-measure-learn/README.md)
- Closure section ← post-build; feeds pivot-or-persevere decision

### 9. Wardley-Map dependency check (if applicable)

If the MVP depends on architecture decisions about technology stack / build-vs-buy, link to the relevant Wardley Map at [`phase-d-technology-architecture/wardley-maps/`](../../../phase-d-technology-architecture/wardley-maps/). If no Wardley Map exists yet but should: queue one.

## Authoring rules

- Length cap: ≤ 600 words. If longer, the MVP is too big.
- Out-of-scope MUST be explicit (not "everything else"). Each item in out-of-scope cites a rationale.
- Kill criteria MUST be pre-committed. "We'll see how it goes" is not a kill criterion.
- Riskiest assumptions MUST be testable by the MVP. If the MVP doesn't test the assumption, the MVP is wrong-shape.

## Measurable motivation chain

Per [P7](../../../phase-preliminary/architecture-principles.md):

- **Driver**: without an MVP-sketch template, MVP scope drifts; teams over-build (Maurya's "Premature Launch" failure mode).
- **Goal**: [Architect-velocity](../../../phase-a-architecture-vision/goals.md) (KR: ≤ 20 execution failures / 30-day rolling). Pre-committed kill-criteria + explicit scope = fewer architect interventions per Build cycle.
- **Outcome**: this template is the canonical MVP-sketch schema.
- **Measurement source**: audit-predicate: P26 + P29.
- **Contribution**: forces design discipline (out-of-scope explicit; kill-criteria pre-committed); reduces build-then-pivot cycles.
- **Capability realised**: [Develop wiki product line](../../capabilities/develop-wiki-product-line.md).
- **Function**: Schema-MVP-sketch.
- **Element**: this template file.
