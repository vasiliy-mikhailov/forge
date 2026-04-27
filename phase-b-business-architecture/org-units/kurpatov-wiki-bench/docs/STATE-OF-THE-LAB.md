# State of the Lab — capability trajectories

`phase-b-business-architecture/org-units/kurpatov-wiki-bench`. The goal: a reproducible, model-agnostic
harness that compiles all ~200 Курпатов lecture transcripts into a
structured wiki at-or-better-than Claude Opus baseline. Architecture
management is capability-based per `forge/CLAUDE.md` ("TOGAF-style
lite"): each capability has Level 1 (as-is) and Level 2 (to-be).

---

## Capability: Compile a Курпатов lecture into a wiki source.md

**Level 1 (as-is)**
The skill v2 ritual (`kurpatov-wiki-wiki:skill-v2/skills/benchmark/SKILL.md`)
defines a 12-step per-source process. Source-author writes
`data/sources/<slug>.md` with frontmatter + 5 sections + claim
markers + Wikipedia URL citations. Concept-curator writes
`data/concepts/<slug>.md` with `## Definition`, `## Contributions by
source`, `## Related concepts` per `wiki/prompts/concept-article.md`.
Production driver: `orchestrator/run-d8-pilot.py` running inside
`kurpatov-wiki-bench:1.17.0-d8-cal` Docker image.

The pilot has been validated on module 005 of "Психолог-консультант"
(7 sources). On Qwen-27B-FP8 the latest pilot produced the source.md
files and concept.md files structurally compliant with skill v2
(L0-L2 + L1.5 in `bench_grade.py`).

**Level 2 (to-be)**
- Production rerun with calibrations applied (curator called for
  every `concepts_touched` slug; `processed_sources` updated;
  density target ≈1 claim per 60s; ru+en Wikipedia URLs cited;
  strict `concepts_introduced ⊂ concepts_touched`) yields
  Opus-parity claim density and REPEATED counts on the same module.
- Wiki concepts conform to canonical skill v2 shape with no L1.5
  violations on `bench_grade --compare-with opus-baseline`.

---

## Capability: REPEATED claim detection (cross-source dedup)

**Level 1 (as-is)**
The idea-classifier sub-agent receives the full
`prior_claims_json` (output of `wiki/skills/benchmark/scripts/get_known_claims.py`)
in its task prompt and decides NEW vs REPEATED via pure LLM
judgement. Works at 7-source scale; degrades past linear-scan
attention budget.

**Level 2 (to-be)**
Retrieval-augmented dedup per ADR 0010 + D8 spec Steps 1-7.
Helpers (`orchestrator/embed_helpers.py`) build a numpy + sqlite
index of prior claims and concepts using
`intfloat/multilingual-e5-base`; classifier calls `find-claims`
to get top-K candidates (~3 KB context) instead of receiving the
full `prior_claims_json` (~250 K tokens at 200 sources). Steps 1-3
GREEN (validated by `tests/synthetic-orchestrator/step8_smoke.py`).
Steps 4-7 (orchestrator integration, pilot bench, scale test,
manual concept-merge audit) pending.

---

## Capability: Top-orchestrator that processes N sources sequentially

**Level 1 (as-is)**
Python `for` loop in `run-d8-pilot.py` creates a fresh
`Conversation` per source, sends a master prompt limited to that
source, runs to completion, then loops. Top-orchestrator
state.events stay flat (≈6 events per source) and never accumulate
across sources. Validated end-to-end on 7 production sources.

**Level 2 (to-be)**
Same shape; no architectural change planned. The Level 2 work for
this capability is to extend the same pattern to 200+ sources
without regression.

---

## Capability: Brainstorm experiments

**Level 1 (as-is)**
Triggered by metric gaps (e.g. claims_total -31 % vs Opus). Single
architect drives. The activity is a single session that:
1. surveys current Level 1 of each affected capability
2. proposes the next Level 2 (a concrete experiment + falsification
   criteria + expected metric delta)
3. prunes documentation that no longer contributes to any
   capability's Level 1 or Level 2 — improves time-to-market and
   token efficiency for the next agent reading the lab

Output: a new `docs/experiments/<id>.md` (Level 2 proposal) +
deletions in any docs that contain stale historical content.

**Level 2 (to-be)**
None planned. The capability works.

---

## Capability: Quantitative grading vs Opus baseline

**Level 1 (as-is)**
`evals/grade/bench_grade.py` produces L0 (parser), L1
(frontmatter), L1.5 (concept canonical shape), L2 (claims
well-formed) per source + aggregate, with `--compare-with` against
the Opus gold checkout. Skips files starting with `_`. Reports
`claims_total / NEW / REPEATED / CONTRADICTS_FACTS / unmarked`,
Wikipedia citation count, concept count, cross-ref violations.

**Level 2 (to-be)**
None planned beyond the L1.5 layer that just landed. If a future
capability ("track per-claim provenance via vector index") arrives,
add an L2.5 layer.

---

## Capability: All work runs in containers

**Level 1 (as-is)**
`forge/phase-g-implementation-governance/policies/containers.md` codifies the policy.
`kurpatov-wiki-bench:1.17.0-d8-cal` image bakes openhands-sdk +
sentence-transformers + numpy + e5-base + our scripts at
`/opt/forge/`. Build-time smoke runs `step8_smoke.py` inside
the image.

**Level 2 (to-be)**
Module 005 production rerun is the first canonical container-based
result. Older runs (pre-2026-04-27) ran on host venv; those branches
exist on origin but are not citable as canonical bench results.

---

## Open work for module 005 → published

The shortest path remaining (after the pilot v2 in container
finishes):

1. Bench v2 against Opus on module 005, fold any new gaps into the
   above capability trajectories.
2. Promote the calibrated prompts + the L1.5 layer findings into
   `wiki/skills/benchmark/SKILL.md` if any of them belong upstream.
3. D8 retrieval Steps 4-7 → REPEATED detection at Opus parity.
4. Module 005 published as the canonical Qwen-27B-FP8 compilation
   on `experiment/D8-final-<date>-<served>` branch.

---

## Reference

- `forge/CLAUDE.md` § Architecture management — TOGAF-style
  capability trajectories
- `forge/phase-g-implementation-governance/policies/containers.md` — containers-only invariant
- `kurpatov-wiki-wiki:skill-v2/prompts/concept-article.md` — canonical
  concept shape
- `kurpatov-wiki-wiki:skill-v2/skills/benchmark/SKILL.md` — skill v2
  ritual
