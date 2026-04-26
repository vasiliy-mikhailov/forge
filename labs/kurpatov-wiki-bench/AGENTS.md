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
│   ├── openhands-sdk-orchestration.md  # how we use OpenHands SDK; gotchas; canonical patterns
│   └── tdd-on-synthetic-fixtures.md    # progressive TDD methodology for complex agent orchestrations
├── docs/
│   ├── spec.md                         # methodology — hypothesis lifecycle, falsifiability, tier definitions
│   ├── backlog.md                      # ranked hypothesis backlog (A/B/C/D/E/F/G clusters)
│   ├── adr/
│   │   ├── 0001-…0008-…                # earlier infra ADRs
│   │   └── 0009-per-source-agent-isolation.md   # current architecture decision for D7-rev3
│   └── experiments/                    # one .md per experiment with hypothesis, locked falsifiability, results, post-mortem
│       ├── A8.md / F1.md               # closed
│       ├── D7.md                       # skill v2 single-agent — falsified at L0 parser
│       ├── D7-rev2.md                  # skill v2 + 5 env fixes — partial PASS (5/7 sources)
│       └── D7-rev3.md                  # skill v2 + per-source sub-agent isolation — active
├── prompts/
│   ├── launch.md / launch-D7.md / launch-D7-rev2.md   # CLI-mode launch prompts (legacy)
│   └── launch-D7-rev3-orchestrator.md                  # control-flow only; lives in /task at runtime
├── evals/grade/bench_grade.py          # L0-L2 quality grader
├── tests/synthetic/                    # H-Q2/H-Q5 single-agent regression test (4 sources, 10/10 GREEN)
├── tests/synthetic-orchestrator/       # D7-rev3 TDD harness (Python SDK + DelegateTool)
│   ├── .venv/                          # gitignored — openhands-sdk + openhands-tools
│   └── step{1..5,5a}_orchestrator.py   # progressive TDD scripts on synth fixtures
├── configs/models.yml                  # active model registry (single source of truth — ADR 0008)
├── Dockerfile                          # bench sandbox image (PyInstaller openhands binary + curl/python3 wrappers)
├── Makefile / common.mk                # per-lab `make up/down/build/bench`
└── run.sh                              # one-shot bench runner (LAUNCH_PROMPT env-var override supported)
```

## Engineering principles (lab-specific)

These layer on top of the upstream OpenHands AGENTS.md (collaborative software engineering, simplicity, backward compatibility, pragmatic problem-solving). Lab-specific:

1. **Hypothesis-driven experiments.** Every change of substance lives in a numbered experiment doc with hypothesis (IF–THEN–BECAUSE), expected metrics + falsifiability locked **before** the run, and post-mortem after. See `docs/spec.md` for the methodology contract.
2. **One axis at a time.** When a run fails, the post-mortem isolates root causes and proposes the next experiment with one variable changed. Avoid bundling multiple changes into one experimental shot.
3. **Branch hygiene.** `bench/...` for baselines (no skill changes), `experiment/<exp-id>-...` for labelled experiments. Stale branch from a killed run is purged before re-running the same experiment id.
4. **Verify by artifact, not by agent.** When an agent claims it produced something, the verification is a deterministic script (`bench_grade.py --single-source N --json`) reading the file on disk + commit on branch — not the agent's self-report.
5. **Tools-as-contract.** Where the spec calls for behaviour (e.g. fact-check before mark, REPEATED detection), the contract is enforced by mandatory tool invocations whose absence makes the artifact unverifiable. See skill v2 in `kurpatov-wiki-wiki:skill-v2`.

## Active experimental track

D7-rev3: orchestrator + per-source sub-agent isolation via OpenHands SDK Python orchestrator with `DelegateTool`. See `docs/experiments/D7-rev3.md` for the spec and `docs/adr/0009-per-source-agent-isolation.md` for the architectural decision. Concrete how-to lives in skill `openhands-sdk-orchestration`.

## Known issues with metric history

### `bench_grade.py` `CONTRADICTS_FACTS` regex fix (forge:main `1eae7b1`, 2026-04-26)

Earlier the regex required a SPACE between the words: `r"\[CONTRADICTS\s+FACTS\]"`. Skill v2 spec uses an UNDERSCORE: `[CONTRADICTS_FACTS]`. Three earlier baseline / experiment runs may have hidden `claims_CONTRADICTS_FACTS` markers that the parser silently skipped:

- `bench/2026-04-25-claude-opus-4-6-cowork` (Opus baseline) — reported `claims_CONTRADICTS_FACTS_sum=6`. Probably accurate (Opus uses space format).
- `bench/2026-04-25-qwen3.6-27b-fp8` (Qwen baseline, skill v1) — reported `claims_CONTRADICTS_FACTS_sum=0`. Could be 0 because skill v1 did not enforce the marker, or because qwen used underscore. Re-grade is cheap; not yet done.
- `experiment/D7-2026-04-25-qwen3.6-27b-fp8` — reported `claims_CONTRADICTS_FACTS_sum=0`. Almost certainly under-counted; the agent emitted underscore-format markers in source 000 (the only source with skill v2 shape).
- `experiment/D7-rev2-2026-04-26-qwen3.6-27b-fp8` — reported `claims_CONTRADICTS_FACTS_sum=0`. Same suspicion.

After the regex fix the parser now accepts `[CONTRADICTS\s_+FACTS]` (space OR underscore). Retro re-grade of all three branches with the fixed parser is a small task (10 min); pending.

### `claims_REPEATED_sum` requires `get_known_claims.py` cross-source

If a sub-agent does not call `get_known_claims.py` to learn what prior sources already claimed, it cannot mark anything as REPEATED. D7-rev3 Step 5a verified structural compliance (5 sections + Claims block + markers + URLs) but produced `claims_REPEATED_sum=0` because the sub-agent had no access to prior-source claims. This is addressed in D7-rev3 Step 5c — see `docs/experiments/D7-rev3.md` open issues.

## Cross-references

- Upstream OpenHands SDK design principles: <https://docs.openhands.dev/sdk/arch/design>
- Upstream SDK examples (especially 25 / 41 / 42): <https://github.com/OpenHands/software-agent-sdk/tree/main/examples/01_standalone_sdk>
- Skill v2 source of truth: `kurpatov-wiki-wiki:skill-v2/skills/benchmark/SKILL.md`
- Inference endpoint config: `forge/labs/kurpatov-wiki-compiler/configs/models.yml` (per ADR 0008 — single source of truth)
