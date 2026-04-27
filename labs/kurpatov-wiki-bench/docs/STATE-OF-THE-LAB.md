# State of the Lab — As-Is / To-Be / Gaps Audit

**Date:** 2026-04-27
**Scope:** `forge/labs/kurpatov-wiki-bench` — benchmark of open-weight LLMs vs Claude Opus baseline on the task of compiling Russian Курпатов lecture transcripts into a structured wiki.

This document is a snapshot of where we stand, where we want to be, and what stands between us.

---

## 0. North-star — what we're trying to achieve

**Business outcome:** a Russian-language, navigable wiki of all
Курпатов "Психолог-консультант" course lectures (and eventually the
broader catalog — ~200 sources). Each lecture compiles to a structured
`source.md` (TL;DR, lecture retelling, claims with provenance,
fact-checked URLs, theme-grouped ideas). Concepts referenced across
lectures get their own `concept.md` page that links back to every
source mentioning them, with per-source excerpts and timestamps.

**Engineering outcome:** a reproducible, model-agnostic harness that
can compile this wiki using any LLM-backed agent, and grade the result
deterministically against an Opus gold standard. Replays from
`(Dockerfile + transcripts)` only.

We are not yet at either outcome. The asymptote is real and reachable;
the gap is mostly mechanical.

---

## 1. Specs & experiments — as-is / to-be / gaps

| | **As-is** | **To-be** | **Gap** |
|---|---|---|---|
| **D7 (Opus baseline)** | `bench/2026-04-25-claude-opus-4-6-cowork`. 130 claims, 25 REPEATED, 6 CF, 59 concepts on module 005. The yardstick we measure other models against. | Same — gold standard frozen. | (none) — except retrograde regrade with fixed `CONTRADICTS_FACTS` regex pending (see Tech Debt). |
| **D7 (Qwen, single-agent)** | Falsified at L0 parser. 1/7 sources clean. | (closed) | (none) — closed. |
| **D7-rev2** | 5/7 sources after env fixes. Single-agent attention ceiling. Spec at `docs/experiments/D7-rev2.md`. | (closed) | (none) — closed. |
| **D7-rev3** | Per-source agent isolation via DelegateTool. TDD steps 0-7 GREEN on synth. Production partial 4/7 (Wikipedia 429 + DelegateTool deprecated). Spec committed `docs/experiments/D7-rev3.md`. | Document as superseded by D7-rev4-v2 / D8. | (small) — add "superseded-by D8" header. |
| **D7-rev4 / D7-rev4-v2** | TaskToolSet migration; D7-rev4-v2 5/7 in production due to top-orch context bloat. CF=6 (vs CF=0 in D7-rev3) — first wins on contradicts-facts. Branch `experiment/D7-rev4-v2-2026-04-26-qwen3.6-27b-fp8`. | Document as superseded by D8 (Python-loop top-orch fix). | D7-rev4-v2 spec/post-mortem not fully written; D7-rev4.md exists, no D7-rev4-v2 doc. |
| **D8 pilot v1 (host venv)** | 7/7 verified=ok in 100.5 min, 90 claims, 9 REPEATED, 4 CF, 43 concepts. Branch `experiment/D8-pilot-2026-04-26-qwen3.6-27b-fp8`. **Spike** — host venv, not container. Both architectural invariants (top-orch bounded, concept template v3) hold. | Reproduce inside container as canonical D8 pilot v2 — same Qwen-27B-FP8 endpoint, same prompts. | (high-priority next step) — needs `make smoke-d8` rerun in container. |
| **D8 retrieval (Steps 1-7)** | Steps 1-3 GREEN (encode + index roundtrip + find-claims/concepts) via `embed_helpers.py` + `step8_smoke.py`. Validated both on host venv and inside `kurpatov-wiki-bench:1.17.0-d8` image. Steps 4-7 (orchestrator integration, pilot bench, scale test, audit) pending. | All 7 steps GREEN; retrieval orchestrator beats D8 pilot v1 on REPEATED detection by ≥2× and matches Opus's 25 REPEATED. | (active work) — need source-author + idea-classifier prompt update to call `find-claims` instead of `prior_claims_json`, plus `find-concepts` integration in concept-curator. |
| **D8 spec** | `outputs/D8-retrieval-spec.md` draft with Steps 0-7. Steps 0 (Python-loop top-orch) + 0.2 (concept template v3) + 0.3 (containerize) all delivered. | Promoted into `forge/labs/kurpatov-wiki-bench/docs/experiments/D8.md` (matching naming convention). | Doc move + cross-link to ADR 0010 still pending commit. |

---

## 2. ADRs — as-is / to-be / gaps

| | **As-is** | **To-be** | **Gap** |
|---|---|---|---|
| **0001 openhands-on-server** | Committed. | (stable) | — |
| **0002 docker-sandbox-and-storage-root** | Committed. | (stable) | — |
| **0009 per-source-agent-isolation** | Committed. Original draft references DelegateTool; should be revised to reflect TaskToolSet + Python-loop top-orch lessons learned. | Updated rev to mention (a) TaskToolSet replacing DelegateTool, (b) Python-loop top-orch as canonical orchestration shape, (c) the two architectural invariants now codified in `AGENTS.md`. | `outputs/0009-per-source-agent-isolation-rev2.md` exists as draft; not promoted into `docs/adr/`. |
| **0010 retrieval-augmented dedup** | Draft in `outputs/0010-retrieval-augmented-dedup.md`. Status: Proposed. | Status: Accepted, after Step 4-7 of D8 retrieval lands. Promoted into `docs/adr/0010-...`. | Not committed; status not advanced past Proposed. Companion architectural change for Python-loop top-orch is captured in 0010 but should also be its own ADR. |
| **0011-Python-loop-top-orchestrator** (proposed) | Doesn't exist. | New ADR. The Python-loop top-orch is currently captured inside ADR 0010 but it deserves its own ADR because it's a separable design decision. | Need to write. |
| **forge-containers-policy** | Draft in `outputs/forge-containers-policy.md`. Lab-level mirror in `outputs/AGENTS.md`. | Promoted into `forge/AGENTS.md` (or `forge/docs/policies/containers.md`); section in lab AGENTS.md committed. | Not committed; D7-rev3 / D7-rev4-v2 / D8-pilot v1 ran outside container in violation. |

---

## 3. Implementation — as-is / to-be / gaps

| | **As-is** | **To-be** | **Gap** |
|---|---|---|---|
| **Synth orchestrators** (`tests/synthetic-orchestrator/step1...step8`) | step1-step5 (D7-rev3 era, DelegateTool); step5d_rev_v2 (TaskToolSet); step6, step7, step8 (D8-era). All GREEN at time of commit. | Keep step7 (Python-loop + concept v3) and step8 (retrieval) as canonical synth gates. step1-5 archive. | Cleanup: archive old steps with a `legacy/` subdirectory or delete; document which step is the current TDD gate. |
| **Production drivers** (`orchestrator/run-d7-rev3.py`, `run-d7-rev4.py`, `run-d7-rev4-v2.py`, `run-d8-pilot.py`) | All four committed. Latest is `run-d8-pilot.py`. | Keep latest only as canonical; older drivers move to `legacy/`. Eventually `run-d8-final.py` after retrieval lands. | Old drivers clutter the namespace; risk of someone running an outdated one. |
| **`embed_helpers.py`** | New. CLI: `encode / rebuild / update / find-claims / find-concepts`. numpy + sqlite. Pre-built into image. | Adopted by source-author + concept-curator + idea-classifier sub-agents (via terminal tool calls). | Sub-agent prompts not yet updated. Wiki repo's `skills/benchmark/scripts/` still ships `get_known_claims.py` — should add `find_similar_claims.py` (thin shim) and deprecate `get_known_claims.py`. |
| **`bench_grade.py`** | Committed. Has `--single-source / --json / --compare-with`. Counts `_template.md` as a source (4 false violations). No L1.5 layer for concept template v3. | L1.5 added (concept structure validation). Skip `_template.md` glob filter. Output structured Markdown report with violations grouped. | Mechanical patches — see `outputs/skill-v2-SKILL-patch.md` for the L1.5 spec. |
| **wiki helper scripts** (`get_known_claims.py`, `factcheck.py`, `extract_transcript.py`, `list_sources.py`) | Committed in `kurpatov-wiki-wiki:skill-v2/skills/benchmark/scripts/`. `factcheck.py` UA fixed for Wikipedia bot policy. | Add `find_similar_claims.py` and `find_similar_concepts.py` (shims to embed_helpers); add `migrate_concepts_v3.py` for existing baseline regen. | Not yet shipped to wiki repo. |
| **Dockerfile** | `kurpatov-wiki-bench:1.17.0-d8` built and validated (smoke 1-4). 7.13 GB. Includes openhands-sdk + sentence-transformers + e5-base + our scripts in `/opt/forge/`. | Committed to `forge:main`. Image size optimized (~3-4 GB) by not pulling CUDA wheels (CPU-only torch). Multi-stage build to drop pip wheel cache. | Dockerfile patch on server only; not yet committed. CUDA wheel reduction is optional (size is OK for now). |
| **Makefile** | Has `build / bench / preflight / clean-experiments / smoke / up / down`. No D8-aware target. | Add `smoke-d8` (runs `step8_smoke.py` in container) and `bench-d8` (runs `run-d8-pilot.py`). | Mechanical addition; ~5 lines. |

---

## 4. Skills (the ritual contracts) — as-is / to-be / gaps

| | **As-is** | **To-be** | **Gap** |
|---|---|---|---|
| **`kurpatov-wiki-wiki:skill-v2/skills/benchmark/SKILL.md`** | The 12-step per-source ritual is canonical. Specifies `source.md` template, mandatory `factcheck.py` and `get_known_claims.py` calls, marker grammar (`NEW / REPEATED / CONTRADICTS_FACTS`). **Does NOT specify concept-page structure.** | Adds Step 13 ("Concept articles") + a top-level "Concept article template (mandatory)" section per `outputs/skill-v2-SKILL-patch.md`. Adds `find_similar_claims` step replacing `get_known_claims`. | Patch not applied. Patch ready, drafted in `outputs/`. |
| **AGENTS.md** (lab-level, in `forge/labs/kurpatov-wiki-bench/`) | Committed. Has cross-references and known-issues sections. Updated draft in `outputs/AGENTS.md` adds 3 new lab-wide invariants: forge-containers, top-orch context bounded, concept template v3 backlinks. | Draft promoted to repo. | Not committed. |
| **`openhands-sdk-orchestration.md`** (skill in `.agents/skills/`) | Committed. Captures spike findings about DelegateTool / TaskToolSet / file-based sub-agents. Updated draft in `outputs/` adds (a) Top-orch must not span multiple sources, (b) Concept-curator must produce backlinks + per-source excerpts. | Promoted to skill location. | Not committed. |
| **`tdd-on-synthetic-fixtures.md`** | Committed (in lab `.agents/skills/`). | (stable) | — |
| **`concept-template-v3.md`** | Draft in `outputs/`. Standalone spec doc. | Promoted as a section in `wiki/skills/benchmark/SKILL.md`. | Not yet promoted; patch ready. |

---

## 5. Infrastructure & deployment — as-is / to-be / gaps

| | **As-is** | **To-be** | **Gap** |
|---|---|---|---|
| **Inference endpoint** | `https://inference.mikhailov.tech/v1` serving `qwen3.6-27b-fp8`. Behind Caddy. Stable across runs. | Same. | — |
| **Bench Docker image** | `kurpatov-wiki-bench:1.17.0-d8` built and tested. e5-base pre-cached. PyInstaller wrappers retained for backward compat. | Pushed to a registry (or kept local), tagged with image digest in each experiment branch's `bench-report.md`. | Image is local-only; no registry. Not a blocker for single-server work. |
| **Storage** | `/mnt/steam/forge/labs/kurpatov-wiki-bench/experiments/` (per ADR 0002). | Same. | — |
| **Run mode** | D7-rev3 / D7-rev4 / D7-rev4-v2 / D8-pilot v1 all ran on host venv at `tests/synthetic-orchestrator/.venv/` — violates forge-containers policy. D8 pilot v2 will be the first canonical container run. | All experiments run inside container only. | The shift is now mechanically possible (image exists); needs to be enforced via `make` and a code review checklist. |

---

## 6. Open problems / current bugs — as-is / to-be / gaps

| Problem | Symptom | Fix path |
|---|---|---|
| **24 cross-ref violations in D8 pilot v1** | `concepts_touched` lists slugs that have no corresponding `wiki/data/concepts/<slug>.md` because curator was called only for the `concepts_introduced` subset. | Source-author calls curator on every `concepts_touched` slug. With D8 retrieval, the call is preceded by `find_similar_concepts` to detect dedup. |
| **8 cross-ref violations: `concept-index.processed_sources`** | Frontmatter expects this list to grow per source; orchestrator never writes to it. | Add explicit Step F.6 in source-author prompt: append source slug after writing source.md. |
| **Claims density -31% vs Opus** | 90 claims (Qwen, D8 pilot) vs 130 (Opus). Likely cause: `~1 claim / 60s` target too vague — agent rounds down. | Tighter prompt: "for a 50-min lecture, ≈ 50 claims, not 13." |
| **REPEATED -64% vs Opus** | 9 (Qwen) vs 25 (Opus). Linear-scan of `prior_claims_json` plus context dilution. | D8 retrieval (Steps 4-7). |
| **Wikipedia citations -33% vs Opus** | Cite best-only when factcheck.py returns RU+EN. | Update fact-checker sub-agent prompt: cite both URLs when both returned. |
| **`concepts_touched ≡ concepts_introduced`** | Should be a strict subset; source-author treats every touched concept as introduced. | Tighten source-author prompt with explicit list separation. |
| **`bench_grade.py` grades `_template.md` as source** | 4 false violations. | Skip `_template.md` glob; small patch. |
| **Wikipedia HTTP 429 at scale** | At ~150 fact-check calls/hour. | Identifiable User-Agent already applied; add per-call jitter and exponential backoff. |
| **Image size 7.13 GB** | Pulled CUDA wheels for torch despite running on CPU only. | Use `pip install torch --index-url https://download.pytorch.org/whl/cpu`. ~3-4 GB. Optional. |
| **Inline concept-link duplicated in body** | Sometimes `[concept](slug.md) ([concept](slug.md))` — model writes the link twice. | Source-author prompt note: "exactly one inline link per concept first mention." |
| **Wikipedia results not always in lecture's domain** | Fact-checker occasionally cites a tangentially-related article. | Score top-K results; require speaker keyword match before accepting. |

---

## 7. Hypotheses — what we're testing

| Status | Hypothesis | Evidence |
|---|---|---|
| **Confirmed** | Single-agent attention can't sustain 7-source skill v2 ritual on Qwen-27B-FP8. | D7 1/7, D7-rev2 5/7. |
| **Confirmed** | Per-source sub-agent isolation breaks the single-agent ceiling. | D7-rev3 4/4 verified=ok on synth, then partial production. |
| **Confirmed** | DelegateTool's `max_children=5` requires spawn-once-reuse pattern. | D7-rev3 step 5d post-mortem. |
| **Confirmed** | Top-orchestrator state.events accumulation is the next bottleneck. | D7-rev4-v2 stops at 5/7 with cumulative top-orch input 8.93 M tokens. |
| **Confirmed** | Python `for` loop with fresh Conversation per source bounds top-orch context. | D8 pilot v1 7/7, top-orch events = 6 per source. |
| **Confirmed** | Concept template v3 (backlinks + excerpts + timestamps) is producible on Qwen-27B-FP8. | 42/43 concepts pass v3 validator on D8 pilot v1. |
| **Confirmed** | Multilingual e5-base discriminates Russian paraphrases adequately. | step8_smoke: paraphrase 0.93+, unrelated 0.83 max, margin 0.10. |
| **Confirmed** | numpy linear cosine over 6 K vectors is fast enough. | step8_smoke step3 returns top-K in <100 ms. |
| **Active** | D8 retrieval lifts REPEATED detection from 9 to ≥20 (Opus-level 25). | Steps 1-3 GREEN; step 4-5 (orchestrator integration + production rerun) pending. |
| **Active** | D8 retrieval-driven concept dedup eliminates ~30% of duplicate concept candidates. | step8_smoke step3b proves the mechanism; production validation pending. |
| **Active** | The architecture scales to 200 sources without context exhaustion. | Steps 6 (14-source scale test) and 7 (concept-merge audit) pending. |
| **Active** | Containerizing D8 (replicating D8 pilot v1 result inside `kurpatov-wiki-bench:1.17.0-d8`) yields content identical to host-venv result, ±5% wall. | Build smoke + runtime smoke PASS; production rerun pending. |
| **Pending** | Tighter source-author prompt closes claims density gap to ≥110 (vs Opus 130). | Calibration #3 in D8-pilot-results post-mortem. Untested. |
| **Pending** | Calling concept-curator on every `concepts_touched` slug (not just `introduced`) reduces cross-ref violations from 24 to <5. | Calibration #1. Untested. |

---

## 8. Tech debt — sorted by cost-of-not-fixing

| Severity | Item | Cost if not fixed | Effort |
|---|---|---|---|
| **High** | D8 pilot v1 was a host-venv spike, not a canonical container run. Branch `experiment/D8-pilot-...` should be re-baked. | Reproducibility audit fails; results not citable. | ~2 h: rerun in container, replace branch. |
| **High** | Source-author calls curator only for `concepts_introduced`, leaving `concepts_touched ⊃ introduced` slugs unbacked. | 24 cross-ref violations per pilot; navigation breaks. | ~1 h prompt edit + 1 rerun. |
| **High** | `concept-index.json processed_sources` not maintained. | 8 cross-ref violations; orchestrators of future runs can't read prior runs cleanly. | ~30 min prompt edit. |
| **High** | `concept-template-v3` not in `wiki/skills/benchmark/SKILL.md`. | Future model runs have no formal contract for concepts; spec drift continues. | ~30 min: apply patch from `outputs/skill-v2-SKILL-patch.md`. |
| **Medium** | ADR 0009 references DelegateTool as primary; doesn't reflect TaskToolSet + Python-loop. | Confusing for the next person reading. | ~30 min revise rev2. |
| **Medium** | ADR 0010 still Proposed; the architectural decisions inside it (Python-loop, concept v3) are already deployed. | The doc lags reality; reviewer can't tell what's current. | ~15 min status flip + commit after D8 v2 lands. |
| **Medium** | Multiple `run-*.py` drivers in `orchestrator/` (rev3, rev4, rev4-v2, d8-pilot). | New contributor doesn't know which is canonical. | ~30 min: move legacy to `legacy/`, leave `run-d8.py` as canonical. |
| **Medium** | `bench_grade.py` lacks L1.5 layer (concept template). | Concept structure regressions go undetected. | ~1 h: implement validate_concept_v3 (reference impl in `outputs/step7_orchestrator.py`). |
| **Medium** | All four pre-D8 baseline branches need re-grade after `CONTRADICTS_FACTS` regex fix (already in main). | Old `claims_CF` numbers undercount on Opus and other baselines. | ~30 min: re-run bench_grade on each branch + commit fresh report. |
| **Low** | numpy fallback could be replaced with sqlite-vss inside container. | sqlite-vss is faster at 100K+ vectors; we don't have that scale yet. | When/if scale demands. |
| **Low** | Image size 7.13 GB. | Slow `docker pull` on fresh box. | `torch --index-url cpu`. ~30 min experiment + rebuild. |
| **Low** | step1-step6 synth orchestrators clutter `tests/synthetic-orchestrator/`. | Visual noise. | ~15 min: move to `legacy/`. |

---

## 9. Business result — as-is / to-be / gaps

| | **As-is** | **To-be** | **Gap** |
|---|---|---|---|
| **Module 005 of "Психолог-консультант"** (7 sources) | Compiled by Opus (gold) and Qwen-27B-FP8 (D8 pilot v1, spike). Sources structurally compliant; quality −31% claims, −64% REPEATED vs Opus. | Compiled by Qwen at ~Opus parity. | Calibration + retrieval (Steps 4-7 of D8). |
| **Other modules of "Психолог-консультант"** (001 through 010+) | Untouched — only 005 has been processed. | All compiled. Cross-module REPEATED detection works. | Both pieces missing — no orchestrator run yet, no module-aware retrieval index yet. |
| **Other Курпатов courses** (estimated ~150 sources beyond Психолог-консультант) | Untouched. | Compiled. | Same gap × scale. |
| **Concept dictionary** | 42 concepts (D8 pilot v1, Qwen) or 59 (Opus baseline) in module 005. Lots of near-duplicates across courses expected. | Single canonical concept per kebab-slug, deduped via retrieval, with `touched_by` listing every source that mentions it. | D8 retrieval Step 3b + curator update logic. Then a one-time merge/migration. |
| **Public artifact** | Not exposed publicly. Repos at `github.com/vasiliy-mikhailov/kurpatov-wiki-{raw,wiki}` are private. | If/when polished: a navigable web view (each source.md and concept.md as pages, cross-links, search). | Out of current scope. |

---

## 10. The shortest path from here to "module 005 done"

The work-stream that would cleanest deliver a publishable module 005 result, in order:

1. **Apply the D8 pilot calibration backlog** (`outputs/D8-pilot-results.md` § Calibration backlog):
   - Source-author calls curator for every `concepts_touched`.
   - `processed_sources` update step.
   - Density target tightened.
   - Subset `concepts_introduced ⊂ concepts_touched`.
   - bench_grade L1.5 + skip `_template.md`.

2. **Apply the concept-template-v3 patch** to `wiki/skills/benchmark/SKILL.md`.

3. **Ship the four updated docs to forge:main:**
   - `AGENTS.md` (with new invariants).
   - `openhands-sdk-orchestration.md` (with concept-curator update step).
   - `0009-rev2` ADR.
   - `0010` ADR (still Proposed).
   - `forge-containers-policy` (forge-level).

4. **Rerun D8 pilot v2 inside container** (`make smoke-d8` first, then bench).
   Expectation: 7/7 verified=ok, claims ~110-120, REPEATED ~12-15, violations ~5.

5. **D8 Steps 4-7 (retrieval into orchestrator):**
   - Step 4 — orchestrator + retrieval; synth GREEN.
   - Step 5 — production rerun (D8-final v3); REPEATED ≥ 20.
   - Step 6 — 14-source scale test.
   - Step 7 — manual concept-merge audit.

6. **Module 005 published** — `experiment/D8-final-...` branch becomes
   the canonical Qwen-27B compilation. Compared rigorously against
   Opus baseline.

After that, the same harness applied to module 001, 003, etc., scales
naturally. The 200-source goal becomes ~50-80 hours of inference time,
fully unattended, fully replayable.

---

## Sources

- `outputs/D8-pilot-results.md` — empirical post-mortem of pilot v1
- `outputs/D8-retrieval-spec.md` — D8 plan
- `outputs/0010-retrieval-augmented-dedup.md` — ADR
- `outputs/concept-template-v3.md` — concept page spec
- `outputs/forge-containers-policy.md` — containerization policy
- `outputs/AGENTS.md`, `outputs/openhands-sdk-orchestration.md` — lab memory + skill
- `outputs/skill-v2-SKILL-patch.md` — patch for wiki skill spec
- `outputs/embed_helpers.py`, `outputs/step7_orchestrator.py`, `outputs/step8_smoke.py`, `outputs/run-d8-pilot.py` — code
- Server: `kurpatov-wiki-bench:1.17.0-d8` Docker image
- Server: `experiment/D8-pilot-2026-04-26-qwen3.6-27b-fp8` branch
