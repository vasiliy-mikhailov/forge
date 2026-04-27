# kurpatov-wiki-bench — agent context

This lab benchmarks open-weight LLMs on the task of compiling Russian whisper-transcripted lectures into structured wiki articles. The task contract (the "skill v2") is defined upstream in `kurpatov-wiki-wiki:skill-v2` branch.

## Repos this lab spans

- **`vasiliy-mikhailov/kurpatov-wiki-raw`** — input source. Read-only for the bench. Contains `data/<course>/<module>/<source>/raw.json` (whisper segments).
- **`vasiliy-mikhailov/kurpatov-wiki-wiki`** — output target. Branches:
  - `main` — production state (Mac-side Cowork users).
  - `skill-v2` — the 12-step ritual + helper scripts (`get_known_claims.py`, `factcheck.py`, `extract_transcript.py`, `list_sources.py`). All bench experiments check out from here.
  - `bench/<date>-<served-name>` — baseline runs (skill v1).
  - `experiment/<exp-id>-<date>-<served-name>` — labelled experiments (skill v2 + variations).
- **`vasiliy-mikhailov/forge`** (this repo) — bench harness, image, prompts, evals, ADRs, experiment specs.

## Where things live in this lab

```
forge/labs/kurpatov-wiki-bench/
├── AGENTS.md                           # this file
├── .agents/skills/                     # project-scoped skills (auto-loaded by OpenHands SDK)
│   └── openhands-sdk-orchestration.md  # canonical orchestration patterns; SDK gotchas
├── docs/
│   ├── spec.md                         # methodology — hypothesis lifecycle, falsifiability, tiers
│   ├── backlog.md                      # ranked hypothesis backlog
│   ├── STATE-OF-THE-LAB.md             # as-is/to-be/gaps audit (entry point for new contributors)
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
│   ├── .venv/                          # gitignored — openhands-sdk + openhands-tools
│   ├── step7_orchestrator.py           # synth GREEN gate (Python-loop + concept canonical shape)
│   ├── step8_smoke.py                  # retrieval helpers smoke
│   └── embed_helpers.py
├── configs/models.yml                  # active model registry (ADR 0008)
├── Dockerfile                          # bench image kurpatov-wiki-bench:1.17.0-d8-cal
├── Makefile / common.mk                # per-lab `make build/bench/preflight`
└── run.sh                              # legacy CLI entrypoint; canonical = `docker run --entrypoint python3 ... /opt/forge/run-d8-pilot.py`
```

## Engineering principles (lab-specific)

These layer on top of the upstream OpenHands AGENTS.md (collaborative software engineering, simplicity, backward compatibility, pragmatic problem-solving). Lab-specific:

1. **Hypothesis-driven experiments.** Every change of substance lives in a numbered experiment doc with hypothesis (IF–THEN–BECAUSE), expected metrics + falsifiability locked **before** the run, and post-mortem after. See `docs/spec.md` for the methodology contract.
2. **One axis at a time.** When a run fails, the post-mortem isolates root causes and proposes the next experiment with one variable changed. Avoid bundling multiple changes into one experimental shot.
3. **Branch hygiene.** `bench/...` for baselines (no skill changes), `experiment/<exp-id>-...` for labelled experiments. Stale branch from a killed run is purged before re-running the same experiment id.
4. **Verify by artifact, not by agent.** When an agent claims it produced something, the verification is a deterministic script (`bench_grade.py --single-source N --json`) reading the file on disk + commit on branch — not the agent's self-report.
5. **Tools-as-contract.** Where the spec calls for behaviour (e.g. fact-check before mark, REPEATED detection), the contract is enforced by mandatory tool invocations whose absence makes the artifact unverifiable. See skill v2 in `kurpatov-wiki-wiki:skill-v2`.

## Active experimental track

D8: Python-loop top-orchestrator + canonical skill v2 concept shape (`## Contributions by source` per `wiki/prompts/concept-article.md`) + retrieval-augmented dedup. See `docs/experiments/D8.md` for the spec, `docs/adr/0010-retrieval-augmented-dedup.md` for the ADR, and `docs/STATE-OF-THE-LAB.md` for the as-is/to-be audit. Concrete patterns in skill `openhands-sdk-orchestration`.

## Known issues with metric history

### `bench_grade.py` `CONTRADICTS_FACTS` regex now accepts both spellings

Skill v2 produces `[CONTRADICTS_FACTS]` (underscore); Opus baseline runs produced `[CONTRADICTS FACTS]` (space). Regex (`\[CONTRADICTS[\s_]+FACTS\]`) accepts either. Pre-fix bench-reports for `bench/2026-04-25-qwen3.6-27b-fp8`, `experiment/D7-…`, `experiment/D7-rev2-…` show `claims_CONTRADICTS_FACTS_sum=0`; under-counted. Re-grade with current parser if the historical numbers matter for a comparison.

### Forge-wide invariant: all work runs in containers

**Rule (forge-level, applies to every lab):** every executable artifact —
orchestrators, helper scripts, evaluators, retrieval indexes — MUST run
inside a Docker container. No host-Python runs in production. No
host-pip installs of new dependencies.

**Why:** isolation, reproducibility, system-package consistency
(libblas, libssl, glibc). Without containerization, runs become
host-dependent ("works on Vasiliy's server, not on a fresh box"), which
breaks the "every run is replayable from the artifact + Dockerfile"
contract underlying the bench.

**What we drifted on (2026-04-26 audit):** D7-rev3 onwards we ran
orchestrators directly from the Python venv at
`tests/synthetic-orchestrator/.venv/`. Convenient for iteration
(no docker rebuild per change), but breaks the forge contract.

D7-rev2 ran inside a wrapped image (per ADR
`forge:0049-Dockerfile-LD_LIBRARY_PATH-leak`). D7-rev3 dropped that
because openhands-sdk Python imports were easier to iterate without
rebuilding the image. **This was a tactical compromise, not a strategic
shift.** Production-grade runs MUST go back into a container.

**Concrete next steps:**
- Bake `sentence-transformers`, `numpy`, `openhands-sdk`, `openhands-tools`,
  `requests`, `pyyaml` into the bench Docker image (`forge/labs/kurpatov-wiki-bench/Dockerfile`).
- Promote `embed_helpers.py`, `bench_grade.py`, the orchestrator
  drivers (`run-d8-pilot.py`, etc) into `/usr/local/bin/` inside the
  image so `make bench` runs them.
- Container build = single source of truth; venv mode is allowed for
  spike testing only and must be flagged in any post-mortem.

**numpy vs sqlite-vss decision (2026-04-26):** chose numpy fallback
because sqlite-vss requires `libblas3` system package (apt sudo). Inside
the bench container this is trivially `apt install libblas3` — but until
we re-containerize, numpy is the portable path. Either backend works
with the same `embed_helpers.py` API once libblas is present.

### Concept articles: follow canonical skill v2 shape (LAB-WIDE INVARIANT)

**Rule**: every concept article in `wiki/data/concepts/<slug>.md` MUST
match the canonical shape defined in
`kurpatov-wiki-wiki:skill-v2/prompts/concept-article.md`:

```yaml
---
slug:
first_introduced_in: <full source slug>
touched_by:
  - <full source slug>
---
# <Russian title>

## Definition
(2 paragraphs grounded in lecture; optional **How Kurpatov uses this**)

## Contributions by source
### <full source slug>
- bullet on what this source adds
- See [<short title>](../sources/<source-slug>.md). [mm:ss]

## Related concepts
- [other-slug](other-slug.md) — relationship.
```

**Why**: this contract has been in skill v2 since 2026-04-25.
D7-rev3 / D7-rev4-v2 / D8-pilot v1 deviated from it because
`bench_grade.py`'s `REQUIRED_CONCEPT_SECTIONS` was lenient
(`["## Definition"]` only) and the spec gap I "discovered" in
D7-rev4-v2 audit was a confabulation — the spec was always there,
I hadn't read it. Post-mortem: `outputs/concept-template-v3.md`
(WITHDRAWN status).

**Enforcement (bench_grade.py L1.5, post-2026-04-27)**:
- per-concept: `## Contributions by source` present
- per-concept: one `### <slug>` sub-section per `touched_by` entry
- per-concept: each sub-section body ≥ 30 chars
- per-concept: frontmatter has `first_introduced_in`
- skip files starting with `_` (template baselines)

**Concept-curator behavior** (per `prompts/per-source-summarize.md`):
- on NEW concept: create the file from
  `prompts/concept-article.md` (first-introduction prompt)
- on EXISTING concept: append a new `### <source-slug>` sub-section
  under `## Contributions by source`; never edit earlier entries
- update `concept-index.json:processed_sources` after writing source.md

### Top-orchestrator context must NOT grow across sources (LAB-WIDE INVARIANT)

**Rule**: in any orchestrator architecture we adopt going forward, the
top-level orchestrator's conversation history MUST be bounded — ideally
**flat per source** (fresh Conversation per source via Python loop), and
in no case may it accumulate task() / delegate() return values across
all sources.

**Why this is now an invariant:**
D7-rev4-v2 production (2026-04-26, branch
`experiment/D7-rev4-v2-2026-04-26-qwen3.6-27b-fp8`) revealed that
TaskToolSet's fresh-context-per-call semantics fix sub-agent context
bloat but *not* the top-orchestrator's own context. After 5 source-author
task() returns, top-orch input grew to 8.93 M cumulative tokens; the
agent then "forgot" to process sources 5-6 and exited with
`Source 4 processed successfully` — a fresh manifestation of the same
linear-scan attention failure we observed in single-Conversation orchestration.

**Concrete enforcement:**
- Smoke / synth orchestrator MUST assert `top_orch_input_tokens_per_source
  ≤ 100 K` (or fewer, model-dependent). See
  `tests/synthetic-orchestrator/step6_*` (D8 Step 0).
- Production driver MUST instantiate a fresh `Conversation(...)` per
  source inside a Python `for` loop. Long-lived
  `conv.send_message(master_for_all_sources)` followed by
  single `conv.run()` is the anti-pattern.
- Code review for any new run-*.py: confirm Python loop topology
  before merge.

Per-source TOP-orchestrator isolation. Captured in ADR 0010 + D8 spec Step 0.

## Cross-references

- Upstream OpenHands SDK design principles: <https://docs.openhands.dev/sdk/arch/design>
- Upstream SDK examples (especially 25 / 41 / 42): <https://github.com/OpenHands/software-agent-sdk/tree/main/examples/01_standalone_sdk>
- Skill v2 source of truth: `kurpatov-wiki-wiki:skill-v2/skills/benchmark/SKILL.md`
- Inference endpoint config: `forge/labs/kurpatov-wiki-compiler/configs/models.yml` (per ADR 0008 — single source of truth)

## Operational rules (entry points, versioning, secrets)

These were the unique rules from the older `CLAUDE.md` (now merged
here so this file is the single source of truth, with `CLAUDE.md`
as a symlink alias):

- **Entry points are load-bearing surfaces.** For most bench-as-battery
  work that means `run.sh` and `run-battery.sh`. For D8 pilot work,
  it means `orchestrator/run-d8-pilot.py` and the
  `tests/synthetic-orchestrator/step*.py` synth gates. Avoid
  splitting these into many smaller scripts unless there is a
  specific reuse driver.
- **Pin OpenHands SDK version.** Don't use `:latest` in image tags or
  `pip install` lines. Bumping the SDK is a deliberate edit, recorded
  in git history and (if behaviour changes) an ADR.
- **Don't edit vLLM compose from here.** The compiler lab owns vLLM.
  To swap the model, edit `forge/.env` (`INFERENCE_MODEL` /
  `INFERENCE_SERVED_NAME`) and `make kurpatov-wiki-compiler-down &&
  make kurpatov-wiki-compiler` — not from this lab.
- **Don't modify `kurpatov-wiki-wiki/skills/benchmark/SKILL.md` from
  here.** That's the task contract; if it needs updates, do them
  deliberately in the wiki repo.
- **Per-run artifacts are append-only.** No run modifies another
  run's output. Old experiment branches are not rewritten; new
  experiments get new branch names.
- **Don't bake `VLLM_API_KEY` (or any secret) into git-tracked files.**
  `.env.example` exists for shape; `.env` is gitignored and lives
  on disk only.

Useful commands:

- `make preflight` — confirm vLLM is healthy + serving the right
  model (smoke for `bench-as-battery`).
- `make bench` — one bench-battery run end-to-end.
- `INFERENCE_SERVED_NAME=qwen3-32b make bench` — override per-run.
- For D8 pilots: `docker run -d --name d8-pilot-vN ... /opt/forge/run-d8-pilot.py`
  (see latest pilot launch in `docs/experiments/D8.md`).
- `ls -lt runs/ | head` — most recent runs first.
- `jq .exit_code runs/*/summary.json` — quick exit-code overview.
