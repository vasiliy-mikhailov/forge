# kurpatov-wiki-bench — agent context

This file follows the canonical TOGAF ADM Phase A-H structure
(see `forge/phase-g-implementation-governance/lab-AGENTS-template.md`). Read forge-level
`AGENTS.md` first for cross-cutting rules; this file is scoped to
the bench lab.

## Phase A — Architecture Vision

Phase A answers *who* cares about this lab as an architecture, *why*
they care, and *what target state* the lab exists to reach.

**Lab role within forge.** This lab is one of forge's four org units. It realises the following forge-level capabilities for the *wiki-compilation* domain: **R&D** (hypothesis-driven experimentation on agent harness + retrieval), **Product delivery** (each pilot's branch is the canonical wiki output), and **Architecture knowledge management** (skill v2 contract; bench_grade.py as the deterministic verifier).

**Vision (lab-scoped).** Provide the agent harness that compiles
Russian whisper-transcripted lectures into structured wiki articles
(per `kurpatov-wiki-wiki:skill-v2`) and grades open-weight LLMs vs
Claude Opus baseline on that task. Bench is dual-purpose: it is the
*production framework* that produces the canonical wiki, AND the
*benchmark* that measures candidate models against Opus.

**Lab-scoped stakeholders.**

- **Architect of record** (forge-wide; see `forge/AGENTS.md`).
- **Consumer of bench output** = the `kurpatov-wiki-wiki` repo
  itself. Each successful pilot lands compiled source.md +
  concept.md files on an experiment branch; the canonical run gets
  merged to `skill-v2`.
- **Upstream service** = `kurpatov-wiki-compiler`'s LLM inference
  service. Bench is a client.

**Lab-scoped drivers.**

- Need a *deterministic* way to measure model quality (LLM-judge
  alone is insufficient; we need bench_grade.py).
- Single-architect attention budget — every failed pilot run costs
  ~30-60 min of recovery + diagnosis. Hypothesis-driven
  experimentation is the only way to keep architect-velocity high.
- Scale from 7 sources (module 005) to 200 sources without quality
  degradation — drives retrieval-augmented dedup (D8).

**Lab-scoped goals.**

- **Quality parity with Opus** on module 005: claim density,
  REPEATED count (≥ 25), CF count, concept count (≥ 59), structural
  compliance (all_violations = 0).
- **Pilot completion rate** ≥ 95 % (no GPU recoveries mid-run —
  realised jointly with G1 in the compiler lab).
- **Architect-velocity** through hypothesis-driven experimentation;
  every run is a falsifiable test, not a fishing trip.

**Lab-scoped principles.**

- **Hypothesis-driven experiments.** Every change of substance lives
  in a numbered experiment doc with hypothesis (IF–THEN–BECAUSE),
  expected metrics + falsifiability locked **before** the run, and
  post-mortem after. See `docs/spec.md` for the methodology contract.
- **One axis at a time.** When a run fails, the post-mortem isolates
  root causes and proposes the next experiment with one variable
  changed. Avoid bundling multiple changes into one experimental shot.
- **Verify by artifact, not by agent.** When an agent claims it
  produced something, the verification is a deterministic script
  (`bench_grade.py --single-source N --json`) reading the file on
  disk + commit on branch — not the agent's self-report.
- **Tools-as-contract.** Where the spec calls for behaviour (e.g.
  fact-check before mark, REPEATED detection), the contract is
  enforced by mandatory tool invocations whose absence makes the
  artifact unverifiable. See skill v2 in
  `kurpatov-wiki-wiki:skill-v2`.

## Phase B — Business Architecture

This lab realises the following rows of forge-level Phase B
(Kurpatov Wiki product capabilities):

| Capability                             | Quality dimension                          |
|----------------------------------------|--------------------------------------------|
| Compile lecture into source.md         | Fast for reading; ≥ Opus claim density    |
| Cross-source dedup of claims           | No repetitions; REPEATED count ≥ Opus     |
| Fact-check empirical claims            | No fake statements; ≥ Opus citation count|
| Concept extraction + linking           | ≥ Opus concept count; canonical skill v2 shape |
| Benchmark open-weight LLMs vs Opus     | Reproducible from (Dockerfile + transcripts) only |

The first four are realised by the agent harness running the skill
v2 ritual; the fifth is realised by `bench_grade.py` + the
multi-model battery in `configs/models.yml`.

## Phase C — Information Systems Architecture

**Repos this lab spans:**

- **`vasiliy-mikhailov/kurpatov-wiki-raw`** — input source. Read-only
  for the bench. Contains `data/<course>/<module>/<source>/raw.json`
  (whisper segments). Produced upstream by `kurpatov-wiki-ingest`.
- **`vasiliy-mikhailov/kurpatov-wiki-wiki`** — output target.
  Branches:
  - `main` — production state (Mac-side Cowork users).
  - `skill-v2` — the 12-step ritual + helper scripts
    (`get_known_claims.py`, `factcheck.py`, `extract_transcript.py`,
    `list_sources.py`). All bench experiments check out from here.
  - `bench/<date>-<served-name>` — baseline runs (skill v1).
  - `experiment/<exp-id>-<date>-<served-name>` — labelled experiments
    (skill v2 + variations).
- **`vasiliy-mikhailov/forge`** (this repo) — bench harness, image,
  prompts, evals, ADRs, experiment specs.

**Run artefacts** under
`${STORAGE_ROOT}/labs/kurpatov-wiki-bench/experiments/<run_id>/` —
events.jsonl, summary.json, per-source bench-report.md.

**Lab-internal data:**

- Retrieval indices at `wiki/data/embeddings/{claims,concepts}.{sqlite,npz}`
  (numpy + sqlite hybrid; populated by `embed_helpers.py rebuild`).
- Pilot working directories under `/tmp/d8-pilot-vN-prod/` (cleaned
  each run; gitignored).

## Phase D — Technology Architecture

**Service: Agent orchestration & sub-agent delegation** (consumer:
the bench's per-source pipeline).

- Component: OpenHands SDK 1.17.0 + TaskToolSet, file-based sub-agent
  definitions for source-author, idea-classifier, fact-checker,
  concept-curator.
- Component: `orchestrator/run-d8-pilot.py` (Python-loop top-orchestrator).
- L1: bounded top-orch context per source (Invariant — Python-loop
  driver creates fresh `Conversation` per source); 0 % KV-cache reuse
  across sub-agent delegations within a Conversation.
- L2: KV-cache reuse across same-Conversation sub-agent calls (vLLM
  prefix-cache + openhands integration). Estimated impact: ~5-10×
  fewer prefill tokens per source.

**Service: Vector retrieval (claim and concept dedup)** (consumer:
source-author + concept-curator sub-agents).

- Component: `orchestrator/embed_helpers.py` +
  `intfloat/multilingual-e5-base` + numpy + sqlite. Index lives in
  the wiki repo at `wiki/data/embeddings/{claims,concepts}.{sqlite,npz}`.
- L1 claim retrieval: wired into source-author per-claim via
  `find-claims --k 5`; threshold 0.78 for REPEATED (calibrated against
  e5-base paraphrase distribution — see step9 synth gate).
- L1 concept retrieval: NOT wired into curator (curator does naive
  exact-slug `ls` check); `find-concepts` CLI exists but unused.
- L1 cost: per-CLI fork of `embed_helpers.py` re-loads e5-base
  (~280 MB) — ~5 s per invocation.
- L2: `find-concepts` wired into curator with 0.85 dedup threshold;
  `embed_helpers` daemonized so the model loads once per pilot.

**Service: Quality grading vs Opus** (consumer: this lab; output is
deterministic JSON for human or LLM-judge audit).

- Component: `evals/grade/bench_grade.py` (L0 parser, L1 frontmatter,
  L1.5 concept canonical shape, L2 claims well-formed). Supports
  `--single-source / --json / --compare-with`.
- L1: works at module 005 scale; canonical-skill-v2 L1.5 layer landed
  2026-04-27. Skips `_template.md` files.
- L2: L2.5 (per-claim provenance via vector index) — not yet planned.

**Forge-wide services this lab CONSUMES** (cross-link to forge-level
Phase D + provider lab):

- LLM inference — provided by `kurpatov-wiki-compiler` lab.
- Container runtime + GPU isolation — forge-wide.
- Source-of-truth + experiment-branch storage — GitHub.
- Audio → text transcription (upstream of bench) — provided by
  `kurpatov-wiki-ingest` lab.

**Components list (this lab's image):**

- `kurpatov-wiki-bench:1.17.0-d8-cal` Docker image bakes openhands-sdk
  + openhands-tools + sentence-transformers + numpy + e5-base +
  bench scripts at `/opt/forge/`. Build-time smoke runs
  `step8_smoke.py` inside the image.

## Phase E — Opportunities and Solutions

Gap analysis for this lab — which capabilities are not yet at
Level 2.

The canonical gap audit is `docs/STATE-OF-THE-LAB.md`. Read it
first before starting any new experiment in this lab.

## Phase F — Migration Planning

Sequenced experiments closing the Phase E gaps. Specs at
`docs/experiments/<id>.md`. Only Active and Closed-but-still-cited
experiments are kept; superseded ones go to git history per
Phase H.

**Active:** D8 — Python-loop top-orchestrator + canonical skill v2
concept shape (`## Contributions by source` per
`wiki/prompts/concept-article.md`) + retrieval-augmented dedup. See
`docs/experiments/D8.md` for the spec, `docs/adr/0010-retrieval-augmented-dedup.md`
for the ADR. Concrete patterns in skill `openhands-sdk-orchestration`.

**Pilot history (most recent first):**

- `experiment/D8-pilot-2026-04-27-qwen3.6-27b-fp8` — pilot v5 (in
  flight), full retrieval wiring + threshold 0.78 + 400 W power cap.
- v4 (same branch, overwritten): 6/7 sources cleanly before GPU
  crash at SRC 6 — REPEATED=12 partial, beat v2's full 9.
- v2: 7/7 sources, REPEATED=9, claims=246 (overshoots Opus 130),
  all_violations=0. Pre-retrieval; reference for trajectory math.

## Phase G — Implementation Governance

Lab-local rules (cross-cutting rules like containers-only live in
forge-level `AGENTS.md`).

**Branch hygiene.**

- `bench/<date>-<served>` for baselines (no skill changes),
  `experiment/<exp-id>-...` for labelled experiments.
- Stale branch from a killed run is purged (`git push origin --delete`)
  before re-running the same experiment id.
- Per-run artifacts are append-only — no run modifies another run's
  output.

**Versioning + image discipline.**

- **Pin OpenHands SDK version.** No `:latest` in image tags or
  `pip install` lines. Bumping the SDK is a deliberate edit, recorded
  in git history (and an ADR if behaviour changes).
- Bench image tag is the canonical `kurpatov-wiki-bench:<openhands-version>-<extras>`
  (today: `1.17.0-d8-cal`). Build-time smoke must pass before tag is
  used.

**Layer separation.**

- **Don't edit vLLM compose from here.** The compiler lab owns vLLM.
  To swap the model, edit `forge/.env` (`INFERENCE_MODEL` /
  `INFERENCE_SERVED_NAME`) and `make kurpatov-wiki-compiler-down &&
  make kurpatov-wiki-compiler` — not from this lab.
- **Don't modify `kurpatov-wiki-wiki/skills/benchmark/SKILL.md` from
  here.** That's the task contract; if it needs updates, do them
  deliberately in the wiki repo.

**Entry points are load-bearing.**

- For bench-as-battery work: `run.sh` and `run-battery.sh`.
- For D8 pilot work: `orchestrator/run-d8-pilot.py` and the
  `tests/synthetic-orchestrator/step*.py` synth gates.
- Avoid splitting these into many smaller scripts unless there's a
  specific reuse driver.

**Top-orchestrator context bound (LAB-WIDE INVARIANT).**

In any orchestrator architecture, the top-level orchestrator's
conversation history MUST be bounded — flat per source (fresh
Conversation per source via Python loop). Smoke / synth tests assert
`top_orch_input_tokens_per_source ≤ 100 K`. D7-rev4-v2 production
broke this with TaskToolSet's accumulated returns (8.93 M cumulative
tokens after 5 sources). Captured in ADR 0010 + D8 spec Step 0.

**Concept canonical shape (LAB-WIDE INVARIANT).**

Every concept article in `wiki/data/concepts/<slug>.md` MUST match
the canonical shape from
`kurpatov-wiki-wiki:skill-v2/prompts/concept-article.md`:
frontmatter (slug, first_introduced_in, touched_by) + `## Definition`
+ `## Contributions by source` with one `### <full source slug>`
sub-section per touched_by entry + `## Related concepts`. Enforcement
in `bench_grade.py` L1.5 layer (post-2026-04-27).

**Secrets.**

- Don't bake `VLLM_API_KEY` (or any secret) into git-tracked files.
  `.env.example` exists for shape; `.env` is gitignored.

**Containers-only invariant** (forge-wide, applies here too).
Every executable artefact runs inside Docker. No host-Python runs in
production. See `forge/AGENTS.md` and
`forge/phase-g-implementation-governance/policies/containers.md`.

**Useful commands:**

- `make preflight` — confirm vLLM is healthy + serving the right
  model.
- `make bench` — one bench-battery run end-to-end.
- `INFERENCE_SERVED_NAME=qwen3-32b make bench` — override per-run.
- For D8 pilots:
  `docker run -d --name d8-pilot-vN ... /opt/forge/run-d8-pilot.py`
  (see latest pilot launch in `docs/experiments/D8.md`).
- `ls -lt runs/ | head` — most recent runs first.
- `jq .exit_code runs/*/summary.json` — quick exit-code overview.

## Phase H — Architecture Change Management

| Capability | Level 1 (today) | Level 2 (next) | Metric delta |
|------------|-----------------|----------------|--------------|
| Compile lecture into source.md | Python-loop top-orch + skill v2; ~80 claims/long-source on Qwen3.6-27B-FP8 | Same shape; scale to 200+ sources without regression | (steady-state) |
| Cross-source dedup of claims | bulk `prior_claims_json` to classifier (works at 7-source scale) | Retrieval-augmented (`find-claims` per claim, threshold 0.78); REPEATED ≥ Opus's 25 on module 005 | REPEATED 9 (v2) → ≥ 25 (v5+) |
| Concept extraction + linking | Curator does exact-slug `ls` check; concept count 44 vs Opus 59 (−25 %) | `find-concepts` wired into curator (0.85 dedup threshold); concept count → Opus parity | concept count +25 % |
| Top-orch context bound | Python-loop, ~6 events / source, ~0 % cumulative growth | Same shape at 200 sources; no regression | (steady-state) |
| Quality grading | L0/L1/L1.5/L2 + `--compare-with` | L2.5 (per-claim provenance via vector index) — only if needed | (no plan today) |

When Level 2 is reached, it becomes the new Level 1; the prior
Level 1 description is **deleted from docs**. Git history keeps
every prior level.

## Layout (where things live in this lab)

```
forge/labs/kurpatov-wiki-bench/
├── AGENTS.md                           # this file (CLAUDE.md → AGENTS.md symlink)
├── .agents/skills/                     # project-scoped skills (auto-loaded by OpenHands SDK)
│   └── openhands-sdk-orchestration.md  # canonical orchestration patterns; SDK gotchas
├── docs/
│   ├── spec.md                         # methodology — hypothesis lifecycle, falsifiability, tiers
│   ├── backlog.md                      # ranked hypothesis backlog
│   ├── STATE-OF-THE-LAB.md             # Phase E gap audit (entry point for new contributors)
│   ├── adr/
│   │   ├── 0001-… / 0002-… / 0010-…   # current architecture decisions
│   ├── experiments/
│   │   ├── A8.md / F1.md               # closed research records (KV-budget / L* microbench)
│   │   ├── D8.md                       # current experiment spec
│   │   └── D8-pilot-results.md         # most recent pilot post-mortem
├── orchestrator/
│   ├── run-d8-pilot.py                 # canonical production driver
│   └── embed_helpers.py                # D8 retrieval (encode/index/find-claims/find-concepts)
├── evals/grade/bench_grade.py          # L0-L2 quality grader (+ L1.5 concept template)
├── tests/synthetic/                    # H-Q2/H-Q5 single-agent regression test
├── tests/synthetic-orchestrator/
│   ├── step7_orchestrator.py           # synth GREEN gate (Python-loop + concept canonical shape)
│   ├── step8_smoke.py                  # retrieval helpers smoke
│   └── step9_orchestrator.py           # retrieval-driven REPEATED synth gate
├── configs/models.yml                  # active model registry (ADR 0008)
├── Dockerfile                          # bench image kurpatov-wiki-bench:1.17.0-d8-cal
├── Makefile / common.mk                # per-lab `make build/bench/preflight`
└── run.sh                              # bench-battery CLI entrypoint
```

## Cross-references

- Forge-level: `forge/AGENTS.md` (Phase A vision + cross-cutting
  rules; Phase D service tenancy table).
- Template: `forge/phase-g-implementation-governance/lab-AGENTS-template.md`.
- Upstream OpenHands SDK design principles:
  <https://docs.openhands.dev/sdk/arch/design>
- Upstream SDK examples (especially 25 / 41 / 42):
  <https://github.com/OpenHands/software-agent-sdk/tree/main/examples/01_standalone_sdk>
- Skill v2 source of truth:
  `kurpatov-wiki-wiki:skill-v2/skills/benchmark/SKILL.md`.
- Inference endpoint config:
  `forge/labs/kurpatov-wiki-compiler/configs/models.yml` (per
  ADR 0008 — single source of truth).
