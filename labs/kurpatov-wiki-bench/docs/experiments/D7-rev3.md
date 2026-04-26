# D7-rev3 — orchestrator + per-source sub-agent isolation

Active spec. Methodology: [`../spec.md`](../spec.md). Backlog:
[`../backlog.md`](../backlog.md). Predecessors: [`D7.md`](D7.md), [`D7-rev2.md`](D7-rev2.md).
Architectural decision: [`../adr/0009-per-source-agent-isolation.md`](../adr/0009-per-source-agent-isolation.md).

## Hypothesis (IF–THEN–BECAUSE)

> **IF** we run the same skill v2 stack used in D7-rev2 (12-step ritual + path
> fix + factcheck.py SSL/empty-result fixes + Dockerfile shell wrappers +
> Cyrillic-pinned launch prompt), but instead of a single agent processing
> all 7 sources in one OpenHands session, we use an **orchestrator agent**
> that does control-flow only (clone + branch + per-source delegate +
> per-source verify + final report) and delegates each source to a
> **fresh sub-agent** via the OpenHands SDK CLI 1.17.0 `task` tool, scoped
> to a per-source-N subdir of the shared workspace,
> **THEN** all 7 sources of module 005 will be authored at full skill v2
> compliance (frontmatter + 5 sections + Claims block with markers + URL
> citations from `factcheck.py`), closing the 5/7 → 7/7 gap left by D7-rev2,
> **BECAUSE** D7-rev2 demonstrated empirically that with environmental
> friction removed (5 distinct fixes applied, all individually validated)
> the binding constraint becomes the single agent's per-source attention
> budget — and per-source agent isolation removes that constraint by
> giving each source a fresh context on a fresh agent.

## Architecture: as-is vs. to-be

### As-is (D7-rev2, 5/7 sources clean)

```
agent (one OpenHands session, one CodeActAgent instance, accumulating context)
 ├─ source 000: ✓ skill v2 full ritual (~3 min wall, ~80K context at done)
 ├─ source 001: ✓ skill v2 full ritual (~5 min wall, ~150K context at done)
 ├─ source 002: ✓ skill v2 full ritual (~5 min wall, ~220K context at done)
 ├─ source 003: ✓ skill v2 full ritual (~5 min wall, ~290K context at done)
 ├─ source 004: ✓ skill v2 full ritual (~3 min wall, ~340K context at done)
 ├─ source 005: ✗ NOT authored — agent declared task complete
 └─ source 006: ✗ NOT authored — same

bench-report.md: NOT written (agent didn't reach loop-end)
```

### To-be (D7-rev3)

```
orchestrator (one OpenHands session, ~5K context throughout entire run)
 ├─ STEP 0: clone raw + wiki to /workspace/{raw,wiki}; branch from skill-v2
 ├─ STEP 1: list_sources.py → [000..006]
 ├─ STEP 2: for N in 0..6:
 │   ├─ mkdir /workspace/source-N; copy raw, wiki into it
 │   ├─ task tool call: delegate to fresh sub-agent
 │   │     description: "process source N"
 │   │     prompt: <skill v2 scoped to source N at /workspace/source-N>
 │   │     ↓
 │   │   sub-agent (fresh CodeActAgent, empty context):
 │   │     - reads SKILL.md fresh
 │   │     - extract_transcript.py N from /workspace/source-N/raw
 │   │     - get_known_claims.py from /workspace/source-N/wiki
 │   │     - factcheck per empirical claim
 │   │     - write source.md, run self-verify, commit, push
 │   │     - returns: "done" | "failed: <reason>"
 │   ├─ orchestrator runs verify-source.sh /workspace/source-N → JSON metrics
 │   └─ orchestrator: if verified=fail → fail-fast; else accumulate state
 ├─ STEP 3: write bench-report.md from accumulated per-source JSON
 └─ STEP 4: commit + push bench-report.md, finish
```

Crucially the orchestrator **never sees** transcripts, source.md content, factcheck JSON output, or per-claim reasoning. Its context grows by ~150-200 tokens per source (the verify-source.sh JSON + the sub-agent ack), totalling ~1.5K added across all 7 sources.

## Contract

### Orchestrator → sub-agent (via `task` tool)

```json
{
  "description": "process source N",
  "prompt": "<scoped skill v2 task — see template below>"
}
```

Sub-agent prompt template (to be templated with `N`, `branch`, `workdir`):

```
You are processing source N={N} of module 005 of course "Психолог-консультант".

WORKDIR: {workdir} (e.g. /workspace/source-{N})
This directory contains a fresh `raw/` and `wiki/` clone. Work ONLY in this
directory. Do not touch `/workspace/source-*/` for other sources.

BRANCH: {branch} (e.g. experiment/D7-rev3-2026-04-26-qwen3.6-27b-fp8)
The wiki clone is already on this branch. After your work, commit + push.

TASK: read {workdir}/wiki/skills/benchmark/SKILL.md and execute the 12-step
ritual on source {N} ONLY. Do NOT iterate to other sources. After commit +
push of source {N}, return.

CYRILLIC PATHS: course = `Психолог-консультант`, module = `005 Природа
внутренних конфликтов. Базовые психологические потребности`. Use literally,
do not romanize.

RETURN CONTRACT: your final `finish` tool call must contain ONLY one of these
two messages, with no surrounding prose:
  - "done"           — source N's source.md and concept articles committed and pushed
  - "failed: <reason>" — unrecoverable failure; <reason> is one short line

You may retry transient failures (e.g. Wikipedia 503) up to 3 times yourself.
Do not retry on missing transcript, malformed raw/, or git-push rejection;
those are unrecoverable from your side — return failed.
```

### Sub-agent → orchestrator (via `task` tool observation)

The `task` tool's observation captures the sub-agent's final `finish` message verbatim. Orchestrator parses for "done" prefix vs "failed:" prefix. Anything else is treated as failed (malformed contract).

### Orchestrator → verify-source.sh (deterministic)

```bash
verify-source.sh /workspace/source-{N}
```

Returns JSON to stdout:

```json
{
  "verified": "ok" | "fail",
  "commit_sha": "abc1234",
  "source_file": "data/sources/.../000 Вводная....md",
  "frontmatter_ok": true,
  "sections_count": 5,
  "has_claims_section": true,
  "claims_total": 14,
  "claims_NEW": 9,
  "claims_REPEATED": 3,
  "claims_CF": 1,
  "claims_unmarked": 0,
  "wiki_url_count": 11,
  "concepts_introduced_count": 4,
  "violations": []
}
```

`verified=ok` requires: frontmatter present, ≥5 sections, Claims block present, claims_total > 0, claims_unmarked = 0. Anything else → `verified=fail` with violation list. Implementation: thin wrapper around `bench_grade.py --single-source N --json` (logic already exists; just needs flag).

### Orchestrator's per-source state slot (accumulator)

```json
{
  "source_n": 5,
  "ack": "done",
  "verify": { /* full verify JSON above */ }
}
```

Total state at end of run: 7 such slots ≈ 1.5K tokens. Plus initial prompt ≈ 3-5K. Total orchestrator context ≈ 5-7K through entire run, well below any model limit.

### Failure policy

Per ADR 0009 §Decision (4): orchestrator does **fail-fast**. If sub-agent returns "failed" OR verify-source.sh returns `verified=fail`, the orchestrator stops the run, surfaces the per-source state to operator, does NOT continue to N+1. Sub-agent owns transient retries internally.

## Falsifiability criteria (locked before run)

D7-rev3 is **falsified** if any one of the following holds on the new branch's bench-grade after the experiment:

- Fewer than **6/7 sources** at full skill v2 compliance (i.e. each with verified=ok).
- Any source with `claims_unmarked > 5` — sub-agent isolation didn't enforce marker discipline.
- Aggregate `fact_check_citations_sum < 30` — sub-agents didn't make factcheck.py invocations stick.
- Aggregate `claims_REPEATED_sum < 5` — `get_known_claims.py` cross-source detection broke under isolation (the per-source workdir means each sub-agent's `get_known_claims.py` only sees what's been pushed to remote and pulled into its workdir; if isolation broke this signal, REPEATED count collapses).

D7-rev3 is **partially confirmed** if 6/7 sources are clean and 1/7 fails on a single specific issue (e.g. one source has a degenerate transcript). Then we accept the partial and document the corner case.

D7-rev3 is **fully confirmed** if 7/7 sources clean. In that case orchestrator + sub-agent isolation becomes the production architecture, and the next experiments shift back to model-axis (B-cluster) or skill-axis (D-cluster).

## Expected metrics (predictions, locked before run)

Comparison plane:
- **base** = baseline Qwen3.6-27B-FP8 + skill v1 (`bench/2026-04-25-qwen3.6-27b-fp8`)
- **D7 #1** = same model + skill v2 single-agent, no env fixes (`experiment/D7-2026-04-25-...`)
- **D7-rev2** = same model + skill v2 single-agent + 5 env fixes, 5/7 sources (`experiment/D7-rev2-2026-04-26-...`)
- **opus** = gold Opus 4.6 + skill v1 (`bench/2026-04-25-claude-opus-4-6-cowork`)
- **D7-rev3 expected** = same model + skill v2 + per-source sub-agent isolation, 7/7 sources

| metric                            | base  | D7 #1 |  D7-rev2 |  opus | D7-rev3 expected     |
| --------------------------------- | ----: | ----: | -------: | ----: | -------------------- |
| `sources_count` (excl. _template) |     7 |     7 |        5 |     7 | 7                    |
| `claims_total_sum`                |    38 |     0 |       80 |   130 | ≥ 110                |
| `claims_NEW_sum`                  |    22 |     0 |       69 |    99 | ≥ 80                 |
| `claims_REPEATED_sum`             |     0 |     0 |       11 |    25 | ≥ 15                 |
| `claims_CONTRADICTS_FACTS_sum`    |     0 |     0 |        0 |     6 | ≥ 3                  |
| `claims_unmarked_sum`             |    16 |     0 |        0 |     0 | 0                    |
| `notes_flagged_sum`               |     4 |     0 |        1 |    18 | ≥ 6                  |
| `fact_check_citations_sum`        |     0 |     0 |       87 |    43 | ≥ 80 (D7-rev2 already over) |
| `fact_check_performed_count`      |     7 |     1 |        5 |     7 | 7                    |
| `concepts_count`                  |    16 |    27 |       20 |    59 | ≥ 35                 |
| spec compliance violations        |   ≥ 5 |   145 |        6 |     5 | ≤ 5                  |

The biggest expected jumps from D7-rev2 → D7-rev3 are: `sources_count` 5 → 7, `claims_total` 80 → 110+, `claims_REPEATED` 11 → 15+, `claims_CONTRADICTS_FACTS` 0 → 3+. The CONTRADICTS jump is the riskiest prediction — depends on sub-agents looking harder at Wikipedia content than the rushed single-agent did.

## Methodology

### Branch naming

`experiment/D7-rev3-<YYYY-MM-DD>-<served-name>`. Example:
`experiment/D7-rev3-2026-04-26-qwen3.6-27b-fp8`. Stale branch from any prior killed attempt of this experiment is purged before run.

### Skill / image / launch versions

- `kurpatov-wiki-wiki:skill-v2` HEAD must be ≥ `9ef4529` (factcheck.py with fallback ladder + curl-cleaned-LD_LIBRARY_PATH path + path-bug fix).
- `kurpatov-wiki-bench` Docker image — built from `forge:main` ≥ `853bf2c` (Dockerfile shell wrappers + 4-phase build smoke).
- New launch prompts:
  - `prompts/launch-D7-rev3-orchestrator.md` — short, control-flow-only.
  - `prompts/sub-agent-source-author.md` — full skill v2 ritual scoped to one source (templated by orchestrator with N/branch/workdir).
- New script: `evals/grade/verify_source.sh` OR `bench_grade.py --single-source N --json`.

### Pre-run checklist

1. Verify GPU 0 (Blackwell) is healthy; vLLM running with served-name `qwen3.6-27b-fp8`.
2. Verify the three pre-conditions above (ref `9ef4529` skill, `853bf2c` image, prompts + verify script committed to forge:main).
3. Verify stale `experiment/D7-rev3-...` branch is purged on github (if any).
4. Run `LAUNCH_PROMPT=prompts/launch-D7-rev3-orchestrator.md ./run.sh`.

### Run plan

1. Orchestrator boots in shared workspace `/workspace`.
2. Orchestrator clones raw + wiki, switches wiki to `skill-v2`, creates and pushes empty experiment branch.
3. Orchestrator iterates sources 000..006 sequentially, each via `task` tool call.
4. After each `task` returns, orchestrator runs verify-source.sh, accumulates state, fail-fast on `verified=fail`.
5. After loop completes, orchestrator writes `bench-report.md` to wiki root, commits, pushes.
6. Orchestrator calls `finish` with summary.

### Verification

Post-run, run `bench_grade.py /workspace/wiki --compare-with /tmp/opus-baseline` to produce the metrics table above.

## Execution log

| run_id                                       | date       | tier | params                                                       | status    | artifact                                                                |
| -------------------------------------------- | ---------- | ---- | ------------------------------------------------------------ | --------- | ----------------------------------------------------------------------- |
| (pending)                                    | 2026-04-26 | T4   | qwen3.6-27b-fp8 + skill v2 + per-source sub-agent isolation  | _pending_ | branch `experiment/D7-rev3-2026-04-26-qwen3.6-27b-fp8`                  |

## Results (filled after run)

_Pending — will record bench-grade table + diff against base / D7 #1 / D7-rev2 / opus columns above._

## Post-Mortem & Insights

_Pending._
