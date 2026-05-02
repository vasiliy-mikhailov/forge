# State of the Lab — capability trajectories

`phase-c-information-systems-architecture/application-architecture/wiki-bench`. The goal: a reproducible,
model-agnostic harness that compiles all ~200 Курпатов lecture
transcripts into a structured wiki at-or-better-than Claude Opus
baseline. Architecture management is capability-based per
`forge/AGENTS.md` Phase H ("Architecture Change Management"): each
capability has Level 1 (today) and Level 2 (next).

When Level 2 is reached, it becomes the new Level 1; the prior L1
description is deleted (git is the archive). The state below reflects
the post-publish-of-module-005 state (2026-04-27).

---

## Capability: Compile a Курпатов lecture into a wiki source.md

**Level 1 (today, post-publish)**

Module 005 of "Психолог-консультант" published as canonical
Qwen3.6-27B-FP8 compilation, tagged
`canonical/qwen3.6-27b-fp8/module-005/2026-04-27` on the wiki repo's
`skill-v2` branch (merge commit `3fd8b18`). The skill v2 ritual
(`kurpatov-wiki-wiki:skill-v2/skills/benchmark/SKILL.md`) defines a
12-step per-source process. Source-author writes
`data/sources/<slug>.md` with frontmatter + 5 sections + claim
markers + Wikipedia URL citations. Concept-curator writes
`data/concepts/<slug>.md` in canonical skill v2 shape (`## Definition`,
`## Contributions by source` with `### <source-slug>` per touched_by,
`## Related concepts`). Production driver:
`orchestrator/run-d8-pilot.py` running inside
`kurpatov-wiki-bench:1.17.0-d8-cal` Docker image.

Pilot v5 metrics on module 005, vs Opus baseline:
- claims_total 240 vs Opus 130 (+85 % — overshoot, calibration target)
- claims_REPEATED 21 vs Opus 25 (−16 %)
- claims_CONTRADICTS_FACTS 5 vs Opus 6 (−17 %)
- claims_unmarked 0 (parity)
- fact_check_citations 52 vs Opus 43 (+21 %, beats Opus)
- concepts_count 48 vs Opus 59 (−19 %)
- all_violations 3 vs Opus 5 (−40 %, structurally cleaner than Opus)
- 7/7 sources verified=ok; 169-min wall on Blackwell at 400 W cap.

**Level 2 (to-be)**

Scale the same pilot driver to 200+ sources (Курпатов "Психолог-консультант"
catalog) without quality regression. Specifically: claims/source,
REPEATED rate, and concepts/source remain at-or-near module 005
levels when the prior corpus has 200 indexed sources rather than 6.

---

## Capability: REPEATED claim detection (cross-source dedup)

**Level 1 (today, post-publish)**

Retrieval-augmented dedup per ADR 0010 + D8 spec Steps 4-7. Helpers
(`orchestrator/embed_helpers.py`) build a numpy + sqlite index of
prior claims and concepts using `intfloat/multilingual-e5-base`.
Source-author calls `find-claims` per claim (top-K=5,
threshold ≥ 0.78 for REPEATED) and feeds candidates to the
idea-classifier instead of the bulk `prior_claims_json`. Validated
synth-side by `tests/synthetic-orchestrator/step9_orchestrator.py`
(2/2 sources, REPEATED=2 on the paraphrased fixture). Validated
production-side by pilot v5: 21 REPEATEDs across module 005,
84 % of Opus's 25.

**Level 2 (to-be)**

Wire `find-concepts` into the concept-curator the same way
`find-claims` is wired into the source-author. Curator's "exists?"
check moves from naive exact-slug `ls` to semantic similarity
(threshold ≥ 0.85). This closes the concept-count gap (48 vs Opus
59) and indirectly improves REPEATED by reducing duplicate
slug-variants of the same concept. Captured in task #1 in the
forge task tracker.

---

## Capability: Top-orchestrator that processes N sources sequentially

**Level 1 (today)**

Python `for` loop in `run-d8-pilot.py` creates a fresh `Conversation`
per source, sends a master prompt limited to that source, runs to
completion, then loops. Top-orchestrator state.events stay flat
(6 events per source) and never accumulate across sources. Validated
end-to-end on module 005 (7 sources × 6 events = 42 events total
across the entire run; 0 % growth).

**Level 2 (to-be)**

Same shape; no architectural change planned. The Level 2 work for
this capability is to extend the same pattern to 200+ sources
without regression — covered jointly with the "Compile lecture"
capability above.

---

## Capability: Quantitative grading vs Opus baseline

**Level 1 (today)**

`evals/grade/bench_grade.py` produces L0 (parser), L1 (frontmatter),
L1.5 (concept canonical shape), L2 (claims well-formed) per source +
aggregate, with `--compare-with` against the Opus gold checkout.
Skips files starting with `_`. Reports
`claims_total / NEW / REPEATED / CONTRADICTS_FACTS / unmarked`,
Wikipedia citation count, concept count, cross-ref violations.

**Level 2 (to-be)**

None planned. If a future capability ("track per-claim provenance via
vector index") arrives, add an L2.5 layer.

---

## Capability: All work runs in containers

**Level 1 (today)**

`forge/phase-g-implementation-governance/policies/containers.md`
codifies the policy. `kurpatov-wiki-bench:1.17.0-d8-cal` image bakes
openhands-sdk + sentence-transformers + numpy + e5-base + bench
scripts at `/opt/forge/`. Build-time smoke runs `step8_smoke.py` and
`step9_orchestrator.py` inside the image.

Module 005's canonical compilation (D8 pilot v5,
2026-04-27) is the canonical container-based result. Pilot driver
mounts orchestrator, embed_helpers, and bench_grade from the host
forge tree at runtime so iteration doesn't require a rebuild.

**Level 2 (to-be)**

None planned.

---

## Capability: Brainstorm experiments

**Level 1 (today)**

Triggered by metric gaps. Single architect drives. The activity is a
single session that surveys current Level 1 of each affected
capability, proposes the next Level 2 (a concrete experiment +
falsification criteria + expected metric delta), and prunes
documentation that no longer contributes to any capability's Level 1
or Level 2.

Output: a new `docs/experiments/<id>.md` (Level 2 proposal) +
deletions in any docs that contain stale historical content.

**Level 2 (to-be)**

None planned. The capability works.

---

## Reference

- `forge/AGENTS.md` § Phase B (Business Architecture: forge
  capabilities + lab realisation table) and § Phase H (Architecture
  Change Management: trajectory framework).
- `forge/phase-g-implementation-governance/policies/containers.md` —
  containers-only invariant.
- `kurpatov-wiki-wiki:skill-v2/prompts/concept-article.md` — canonical
  concept shape.
- `kurpatov-wiki-wiki:skill-v2/skills/benchmark/SKILL.md` — skill v2
  ritual.
- Canonical module 005 compilation:
  `kurpatov-wiki-wiki:canonical/qwen3.6-27b-fp8/module-005/2026-04-27`
  (tag on `skill-v2`, merge commit `3fd8b18`).


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
motivation chain inherited from the lab's AGENTS.md.
