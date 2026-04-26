# D7-rev3 — orchestrator + per-source sub-agent isolation

Active spec (revised 2026-04-26 after spike + Steps 0–5a synthetic). Methodology: [`../spec.md`](../spec.md). Backlog: [`../backlog.md`](../backlog.md). Predecessors: [`D7.md`](D7.md), [`D7-rev2.md`](D7-rev2.md). Architectural decision: [`../adr/0009-per-source-agent-isolation.md`](../adr/0009-per-source-agent-isolation.md). How-to skill: [`../../.agents/skills/openhands-sdk-orchestration.md`](../../.agents/skills/openhands-sdk-orchestration.md).

## Hypothesis (IF–THEN–BECAUSE)

> **IF** we run the same skill v2 stack used in D7-rev2 (12-step ritual + path
> fix + factcheck.py SSL/empty-result fixes + Dockerfile shell wrappers +
> Cyrillic-pinned launch prompt), but instead of a single agent processing
> all 7 sources in one OpenHands session, we use a **Python SDK orchestrator**
> (`Conversation` + `Agent(tools=[DelegateTool])`) that does control-flow
> only — clone + branch + per-source delegate + per-source verify + final
> report — and delegates each source to a **fresh sub-agent** (`AgentDefinition`
> registered as `source-author` with the skill-v2 system prompt) via the
> `DelegateTool`, scoped to a per-source-N subdir of the shared workspace,
> **THEN** all 7 sources of module 005 will be authored at full skill v2
> compliance (frontmatter + 5 sections + Claims block with markers + URL
> citations from `factcheck.py`), closing the 5/7 → 7/7 gap left by D7-rev2,
> **BECAUSE** D7-rev2 demonstrated empirically that with environmental
> friction removed (5 distinct fixes applied, all individually validated)
> the binding constraint becomes the single agent's per-source attention
> budget — and per-source agent isolation removes that constraint by
> giving each source a fresh `state.events` context window on a freshly-
> spawned `AgentDefinition` instance.

## Architecture

### As-is (D7-rev2, 5/7 sources clean — see `D7-rev2.md§Results`)

One OpenHands session, one `CodeActAgent` instance, accumulating context across all sources processed in a single `--task` driven loop. Empirical ceiling: ~4–5 sources clean before the agent self-declares the task complete or shifts into bulk shortcut.

### To-be (D7-rev3)

Python orchestrator script `orchestrator/run-d7-rev3.py` (TBD path) inside the bench Docker container. Pseudocode:

```python
register_builtins_agents()                        # required — CLI doesn't auto-load
register_agent("source-author", agent_definition_to_factory(source_author_def), description=…)
register_tool("DelegateTool", DelegateTool)

orch = Agent(llm=llm, tools=[Tool(name="DelegateTool")])
conv = Conversation(agent=orch, workspace="/workspace", visualizer=…)

# Step 1 — clone + branch (one-shot, in Python wrapper, NOT in conversation)
clone_raw_and_wiki(); checkout_skill_v2(); create_experiment_branch()

# Step 2 — per-source loop driven by the Python wrapper
state = []
for n in range(0, 7):
    provision_source_workdir(n)           # mkdir /workspace/source-{n}, copy raw + wiki

    conv.send_message(
        f"Use DelegateTool to spawn id='src{n}' agent_types=['source-author'], "
        f"then delegate task: 'Process source N={n}. raw_path=source-{n}/raw/data/.../{n:03d}/raw.json. "
        f"target_path=source-{n}/wiki/data/sources/.../{n:03d} ….md. Follow your system_prompt.' "
        "After it returns, finish with the sub-agent's reply."
    )
    conv.run()
    ack = parse_finish_message(conv)      # "done" or "failed: ..."

    verify = subprocess.run(["python3", "bench_grade.py",
                             f"/workspace/source-{n}/wiki",
                             "--single-source", str(n), "--single-source-json"])
    verify_json = json.loads(verify.stdout)

    state.append({"n": n, "ack": ack, "verify": verify_json})

    if ack.startswith("failed:") or verify_json["verified"] != "ok":
        write_bench_report(state, partial=True)
        sys.exit(1)                       # fail-fast

# Step 3 — bench-report.md, commit + push
write_bench_report(state)
commit_and_push("bench-report.md")
```

Critically:
- **Master prompt for each `send_message`** is small (~1 KB regardless of transcript length). Transcripts live on disk; sub-agent reads them in its own context.
- **Sub-agent's `finish` reply** is a literal `done` or `failed: <reason>`. Anything longer accumulates in orchestrator's `state.events`.
- **Verification is a Python subprocess**, not an in-conversation tool call. The verify JSON is parsed by the Python wrapper; orchestrator does NOT see the JSON in its context (a small structured ack from the wrapper's logic is enough).
- **Sub-agent's workspace** is `/workspace/source-{n}/`. Sub-agent's `system_prompt` forbids touching other `/workspace/source-*/`.

For the why behind each design choice, see [ADR 0009](../adr/0009-per-source-agent-isolation.md). For the SDK-level how (registration, tool ordering, gotchas), see skill `openhands-sdk-orchestration`.

## Contract

### `source-author` AgentDefinition

```python
source_author = AgentDefinition(
    name="source-author",
    description=("Sub-agent. Given source_n + raw_path + target_path, executes the skill-v2 "
                 "12-step ritual on that ONE source. Reads transcript from disk. Calls "
                 "get_known_claims.py + factcheck.py via terminal. Writes target file with "
                 "skill-v2 shape. Commits + pushes to the experiment branch. Returns 'done' "
                 "or 'failed: <reason>'."),
    tools=["terminal", "file_editor"],
    system_prompt=SOURCE_AUTHOR_SYSTEM_PROMPT,    # full 12-step ritual scoped to one source
)
```

### Per-delegation task message

Orchestrator's `send_message` body, per source:

```
Use DelegateTool spawn id='src{N}' agent_types=['source-author'].
Then delegate task: "Process source N=<N>. raw_path=<rel>. target_path=<rel>.
                    branch=<branch>. Follow your system_prompt."
After sub-agent returns, finish with the reply verbatim.
```

`<rel>` paths are relative to the orchestrator's workspace.

### Sub-agent return

Exactly one of:

- `done` — sub-agent committed and pushed source-N to the experiment branch.
- `failed: <one-line-reason>` — unrecoverable. Sub-agent owns transient retry of network blips up to 3 attempts; only escalates here on permanent issues (transcript missing, malformed raw, repeated push rejection, self-verify keeps failing).

Anything else is a contract violation; Python wrapper treats as `failed: malformed-contract`.

### Verify-source contract

`bench_grade.py /workspace/source-{N}/wiki --single-source N --single-source-json` returns:

```json
{
  "verified": "ok" | "fail",
  "commit_sha": "<short>",
  "source_file": "data/sources/.../{NNN} ….md",
  "frontmatter_ok": true,
  "sections_count": 5,
  "has_claims_section": true,
  "claims_total": 14, "claims_NEW": 9, "claims_REPEATED": 3, "claims_CF": 1, "claims_unmarked": 0,
  "wiki_url_count": 11,
  "concepts_introduced_count": 4,
  "violations": []
}
```

`verified=ok` requires: `frontmatter_ok && sections_count >= 5 && has_claims_section && claims_total > 0 && claims_unmarked == 0`. Else `verified=fail` with violation list. Already implemented and smoke-tested (see `evals/grade/bench_grade.py` after `1eae7b1`).

### Failure policy

Sub-agent owns transient retry. Orchestrator does not retry. On any `failed:` ack OR `verified=fail` from the verify-script, orchestrator stops the run, writes a partial `bench-report.md` indicating where it stopped, and exits non-zero.

## Falsifiability criteria (locked before run)

D7-rev3 is **falsified** if any one holds on the new branch's bench-grade after the experiment:

- Fewer than **6/7 sources** at full skill v2 compliance (each with `verified=ok`).
- Any source with `claims_unmarked > 5` — sub-agent isolation didn't enforce marker discipline.
- Aggregate `fact_check_citations_sum < 30` — sub-agents didn't make `factcheck.py` invocations stick.
- Aggregate `claims_REPEATED_sum < 5` — `get_known_claims.py` cross-source detection broke under the per-source-workdir / per-pull regime (each sub-agent's `git pull` must see prior sub-agents' commits before classification).

D7-rev3 is **partially confirmed** if 6/7 sources are clean and 1/7 fails on a specific identifiable issue (e.g. degenerate transcript). Document corner case, accept partial.

D7-rev3 is **fully confirmed** if 7/7 sources clean. Then orchestrator + sub-agent isolation becomes the production architecture, and the next experiments shift back to model-axis (B-cluster) or skill-axis (D-cluster).

## Expected metrics (predictions, locked before run)

Comparison plane (numbers from already-completed runs):

- **base** = `bench/2026-04-25-qwen3.6-27b-fp8` (Qwen3.6-27B-FP8 + skill v1)
- **D7 #1** = `experiment/D7-2026-04-25-qwen3.6-27b-fp8` (Qwen + skill v2 single-agent, no env fixes)
- **D7-rev2** = `experiment/D7-rev2-2026-04-26-qwen3.6-27b-fp8` (Qwen + skill v2 single-agent + 5 env fixes, 5/7 sources)
- **opus** = `bench/2026-04-25-claude-opus-4-6-cowork` (Opus 4.6 + skill v1)
- **D7-rev3 expected** — Qwen + skill v2 + per-source sub-agent isolation, 7/7 sources

| metric                            | base  | D7 #1 |  D7-rev2 |  opus | D7-rev3 expected     |
| --------------------------------- | ----: | ----: | -------: | ----: | -------------------- |
| `sources_count` (excl. _template) |     7 |     7 |        5 |     7 | 7                    |
| `claims_total_sum`                |    38 |     0 |       80 |   130 | ≥ 110                |
| `claims_NEW_sum`                  |    22 |     0 |       69 |    99 | ≥ 80                 |
| `claims_REPEATED_sum`             |     0 |     0 |       11 |    25 | ≥ 15                 |
| `claims_CONTRADICTS_FACTS_sum`*   |     0 |     0 |        0 |     6 | ≥ 3                  |
| `claims_unmarked_sum`             |    16 |     0 |        0 |     0 | 0                    |
| `notes_flagged_sum`               |     4 |     0 |        1 |    18 | ≥ 6                  |
| `fact_check_citations_sum`        |     0 |     0 |       87 |    43 | ≥ 80                 |
| `fact_check_performed_count`     |     7 |     1 |        5 |     7 | 7                    |
| `concepts_count`                  |    16 |    27 |       20 |    59 | ≥ 35                 |
| spec compliance violations        |   ≥ 5 |   145 |        6 |     5 | ≤ 5                  |

(*) The earlier D7 / D7-rev2 numbers for `claims_CONTRADICTS_FACTS_sum` are suspect — the `bench_grade.py` regex required `[CONTRADICTS FACTS]` (space) but skill v2 spec uses `[CONTRADICTS_FACTS]` (underscore). Fixed in `1eae7b1`. Retro re-grade is a 10-min follow-up. The number for D7-rev3 will be measured with the fixed parser from the start.

## Methodology

### Branch naming

`experiment/D7-rev3-<YYYY-MM-DD>-<served-name>`. Stale branch from any prior killed attempt is purged before run.

### Skill / image / launch versions

- `kurpatov-wiki-wiki:skill-v2` HEAD must be ≥ `9ef4529` (factcheck.py with fallback ladder + curl-cleaned-LD_LIBRARY_PATH path + path-bug fix).
- `kurpatov-wiki-bench` Docker image — built from `forge:main` ≥ `853bf2c` (Dockerfile shell wrappers + 4-phase build smoke). The image must additionally have `openhands-sdk` and `openhands-tools` Python packages installed (separate Dockerfile change as part of D7-rev3 prep).
- `evals/grade/bench_grade.py` ≥ `1eae7b1` (regex fix + `--single-source-json` flag).
- Python orchestrator: `orchestrator/run-d7-rev3.py` (TBD path).

### Pre-run checklist

1. GPU 0 (Blackwell) healthy; vLLM running with served-name `qwen3.6-27b-fp8`.
2. All version pins above met.
3. Stale `experiment/D7-rev3-...` branch purged.
4. Synthetic TDD harness Steps 5b/5c/6 GREEN before going to production (see Open issues below).

### Run plan

1. Bench `run.sh` invokes the Python orchestrator inside the Docker sandbox.
2. Orchestrator clones raw + wiki to `/workspace/{raw,wiki}` (one shared clone), creates experiment branch on the wiki side, pushes empty branch.
3. For each source N in 0..6:
   - mkdir `/workspace/source-{N}/`; copy raw + wiki into it (per-source isolation).
   - delegate `source-author` with `(N, raw_path, target_path, branch)`.
   - On `done` ack: subprocess `bench_grade.py --single-source N --single-source-json`.
   - If `verified=ok`: append to state, continue.
   - Else: stop, write partial bench-report, exit non-zero.
4. After all 7: write `bench-report.md` from accumulated per-source JSON, commit + push.
5. Orchestrator's Python wrapper exits 0.

### Verification (post-run)

`bench_grade.py /tmp/clone-experiment-branch --compare-with /tmp/clone-opus-baseline` produces the metrics table for the Results section below.

## Open issues — to address in synth before production

These are gaps identified at the end of Step 5a that the production run must not fail on. Each addressed in subsequent TDD step on synth, NOT in production.

### Step 5b — get_known_claims.py integration ✓ DONE

Single-level source-author calls `cd wiki && python3 skills/benchmark/scripts/get_known_claims.py` before classification. 4/4 sources verified=ok, claims_REPEATED_sum=5 (synth fixtures 003/004 correctly mark Moore/Everest as REPEATED from sources 001/002). Forge commit `177f6ac`. Step file `tests/synthetic-orchestrator/step5b_orchestrator.py`.

### Step 5c — 3-level orchestration on 1 source ✓ DONE

Top orchestrator → source-author → fan-out per claim to idea-classifier (pure-LLM) + fact-checker (terminal w/ factcheck.py). 1/1 source verified=ok, 1 CONTRADICTS_FACTS caught (1950-Pareto error), 3 real Wikipedia URLs from factcheck.py invocations (verified visible in events). Top orchestrator: 10 events / 25 KB. Forge commit `177f6ac`. Step file `step5c_orchestrator.py`.

### Step 5d — 3-level on 4 sources + concept-curator ✓ DONE

Adds concept-curator (terminal + file_editor): creates `data/concepts/<slug>.md`, updates `concept-index.json`. Idempotent (Mount Everest from src2 not duplicated when src4 references it). Hit DelegateTool's `max_children=5` cap; resolved via spawn-once-reuse pattern (per upstream example 41). 4/4 verified=ok, REPEATED_sum=5, CF=1, URLs=30, concepts=6, top orchestrator 22 events / 37 KB. Wall ~13 min. Forge commit `177f6ac`. Step file `step5d_orchestrator.py`.

### Step 6 — fail-fast end-to-end (PENDING)

Synth fixture with deliberately broken transcript (JSON missing `segments` or unreadable). Source-author should return `failed: <reason>`. Orchestrator wrapper should stop without delegating subsequent sources. Verify partial bench-report shows where it stopped.

### Step 7 — production module 005 (PENDING)

Once Step 6 is GREEN, port to production: real raw transcripts (~30 KB each), real factcheck.py against Wikipedia (over real network), branch push to `experiment/D7-rev3-<date>-<served>`. Run end-to-end. Re-grade against Opus baseline. Fill Results below.

## Execution log

| run_id  | date       | tier | params                                                             | status    | artifact                                           |
| ------- | ---------- | ---- | ------------------------------------------------------------------ | --------- | -------------------------------------------------- |
| (pending) | 2026-04-26 | T4 | qwen3.6-27b-fp8 + skill v2 + per-source SDK isolation, module 005, 7 sources | _pending_ | branch `experiment/D7-rev3-2026-04-26-qwen3.6-27b-fp8` |

## Results (filled after run)

_Pending — will record bench-grade table + diff against base / D7 #1 / D7-rev2 / opus columns above._

## Post-Mortem & Insights

_Pending._
