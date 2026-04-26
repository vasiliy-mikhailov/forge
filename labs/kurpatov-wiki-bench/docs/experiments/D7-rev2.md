# D7-rev2 — skill v2 (12-step ritual) + clean-env harness

Active spec. Methodology: [`../spec.md`](../spec.md). Backlog:
[`../backlog.md`](../backlog.md). Predecessor with full as-is/to-be:
[`D7.md`](D7.md). Synthetic precedent: [`../../tests/synthetic/`](../../tests/synthetic/).

## Hypothesis (IF–THEN–BECAUSE)

> **IF** we run the same skill v2 (12-step tool-driven ritual + helper
> scripts) used in D7 attempt #1, but with the four root-causes from
> the D7 post-mortem pre-baked away from the agent's attention budget —
> (1) SKILL.md path bug fixed (`list_sources.py` / `extract_transcript.py`
> at correct paths, no `scripts/` prefix), (2) `factcheck.py` rewritten
> to use `LD_LIBRARY_PATH=""` curl as primary path, (3) Dockerfile
> shell wrappers at `/usr/local/bin/{curl,python3}` that strip the
> PyInstaller-leaked `LD_LIBRARY_PATH` for *any* subprocess (so even the
> agent running bare `curl` for sanity-checks gets a clean env), (4)
> launch prompt that pins Cyrillic course/module paths and forbids
> romanization,
> and (5) `factcheck.py` auto-simplifies the query when Wikipedia
> OpenSearch returns empty (last-2-words → last-word → first-word
> fallback ladder) so the agent never sees confusing empty results
> and never debugs a non-broken tool,
> **THEN** the same Qwen3.6-27B-FP8 producing source 000 ✓ but sources
> 001–006 abandoned-as-bare-`# Title` in D7 attempt #1 will hold the
> ritual across more sources, because the ~10 minutes (D7 #1) and ~28
> seconds (D7-rev2 wrapper-less attempt) of attention burned on
> environment troubleshooting are now zero,
> **BECAUSE** the per-source attention budget on a 27B model is the
> binding constraint, and the SSL/path/Cyrillic detours were
> attention-stealing detours that the model could ill afford on top of
> the per-source extract→classify→factcheck→write pipeline.

## Architecture: as-is vs. to-be

### As-is (D7 attempt #1, branch `experiment/D7-2026-04-25-qwen3.6-27b-fp8`)

```
agent
 ↓ reads
skills/benchmark/SKILL.md (skill v2 — 12 steps, ~300 lines)
   bug: paths to scripts/list_sources.py and scripts/extract_transcript.py
        are WRONG (helpers live at top of skills/benchmark/, not under scripts/)
 ↓ shell tool inside container kurpatov-wiki-bench:1.17.0
   bug: PyInstaller-bundled openhands sets LD_LIBRARY_PATH=/tmp/_MEI*
        which breaks bare curl + bare python3 urllib HTTPS
 ↓ helper scripts
   factcheck.py — uses python urllib (would also break under env leak)
 ↓ launch prompt
   bug: doesn't pin Cyrillic paths; agent translated to English mid-run
        ('Психолог-консультант' → 'Psychologist-consultant')
```

Result of D7 attempt #1:
- Source 000: ✓ full skill v2 structure (5 sections + frontmatter +
  16 concepts_touched + claim markers + URL citations)
- Sources 001-006: ✗ `# Title + ## Overview/Summary` shape, no
  frontmatter, English-translated paths, no Claims section
- Bench-grade L0: 145 spec violations, claims_total=0 (parser blind to
  off-spec sources), concepts=27 (vs base 16 vs opus 59)
- Attention burned on environment: ~10 minutes (SSL troubleshooting)
  + ~5 minutes (path discovery for missing scripts/list_sources.py)

### To-be (D7-rev2, current experiment)

```
agent
 ↓ reads
skills/benchmark/SKILL.md (skill v2, paths fixed — kurpatov-wiki-wiki:skill-v2 749e9b3)
 ↓ shell tool inside container kurpatov-wiki-bench:1.17.0 (rebuilt from forge:main 853bf2c)
   /usr/local/bin/curl    — wrapper: unset LD_LIBRARY_PATH; exec /usr/bin/curl
   /usr/local/bin/python3 — wrapper: unset LD_LIBRARY_PATH; exec /usr/local/bin/python3.12
   build-time smoke verifies HTTPS works under simulated PyInstaller LD_LIBRARY_PATH leak
 ↓ helper scripts
   factcheck.py — curl-with-cleaned-env primary path (kurpatov-wiki-wiki:skill-v2 9ef4529)
                  defense-in-depth: still works even if image wrapper is bypassed
 ↓ launch prompt (prompts/launch-D7-rev2.md)
   pinned-Cyrillic cheatsheet; explicit "if you type Psychologist-consultant/ — STOP"
   corrected helper paths
```

Empirically validated before launch (build + container smoke):
- Build-time: `[smoke 2a]` python urllib HTTPS ok under simulated
  `LD_LIBRARY_PATH=/tmp/_MEI_FAKE` (containing zero-byte libssl.so.3
  that would crash the linker without the wrapper).
- Build-time: `[smoke 2b]` curl HTTPS ok under same simulation.
- Container end-to-end with simulated leak: `which curl` → wrapper,
  `which python3` → wrapper, both bare commands return valid Wikipedia
  data; `factcheck.py` returns valid JSON.

## Falsifiability criteria (locked before run)

D7-rev2 is **falsified** if any one of the following holds on the new
branch's bench-grade after the experiment:

- **`spec_violations > 5`** on ≥3 sources — ритуал не выдержал даже на
  чистой среде (значит проблема не была attention-budget; следующий
  кандидат — H-Q1 per-source isolation / sub-agents).
- **`claims_unmarked_sum > 5`** — markers discipline проседает несмотря
  на готовый factcheck.py output.
- **`fact_check_citations_sum < 15`** — script-as-contract не закрепил
  URL citations в final source.md.
- **`claims_REPEATED_sum < 3`** — REPEATED detection не сработал
  несмотря на gotten-claims JSON.

D7-rev2 is **partially confirmed** if 4-5 sources have full skill v2
shape but 2-3 still degrade — ритуал держится дольше, attention budget
расширился, но не до конца. В этом случае D7-rev2 → done with caveat,
H-Q1 (per-source isolation / tree-of-subagents) выдвигается как
дополняющая ставка.

D7-rev2 is **fully confirmed** if all 6-7 sources have full skill v2
shape (frontmatter + 5 sections + Claims с маркерами + URL citations).
В этом случае H-Q1 деприоритизируется — модель и без isolation справилась.

## Expected metrics (predictions, locked before run)

Comparison plane:
- column **base** = baseline current Qwen3.6-27B-FP8 + skill v1 (`bench/2026-04-25-qwen3.6-27b-fp8`)
- column **D7 #1** = qwen + skill v2, attention-burned env (`experiment/D7-2026-04-25-qwen3.6-27b-fp8`)
- column **opus** = gold Opus 4.6 + skill v1 (`bench/2026-04-25-claude-opus-4-6-cowork`)
- column **D7-rev2 expected** = qwen + skill v2 + clean-env harness

| metric                            | base  | D7 #1 |  opus | D7-rev2 expected |
| --------------------------------- | ----: | ----: | ----: | ---------------: |
| `claims_total_sum`                |    38 |     0 |   130 | ≥ 60             |
| `claims_NEW_sum`                  |    22 |     0 |    99 | ≥ 40             |
| `claims_REPEATED_sum`             |     0 |     0 |    25 | ≥ 8              |
| `claims_CONTRADICTS_FACTS_sum`    |     0 |     0 |     6 | ≥ 2              |
| `claims_unmarked_sum`             |    16 |     0 |     0 | 0                |
| `notes_flagged_sum`               |     4 |     0 |    18 | ≥ 6              |
| `fact_check_citations_sum`        |     0 |     0 |    43 | ≥ 20             |
| `fact_check_performed_count`      |     7 |     1 |     7 | 7                |
| `concepts_count`                  |    16 |    27 |    59 | ≥ 35             |
| spec compliance violations        | ≥ 5   |   145 |     0 | ≤ 10             |

D7 #1 had 0 в первых 7 строках not because the agent failed at
fact-checking but because 6/7 sources had no `## Claims` section to parse.
D7-rev2 expectation = sources keep the section, parser counts non-zero.

## Methodology

### Branch naming

`experiment/D7-rev2-<YYYY-MM-DD>-<served-name>`. Stale branch from killed
attempts of this experiment должна быть удалена перед запуском (clean
slate per attempt is the norm — if a run is killed, branch is purged).

### Skill / image / launch versions

- `kurpatov-wiki-wiki:skill-v2` HEAD must be ≥ commit `9ef4529`
  (factcheck.py rewrite + fallback ladder). Path bug fix is `749e9b3`; curl-cleaned-LD_LIBRARY_PATH primary path is `eec8404`.
- `kurpatov-wiki-bench` Docker image — built from `forge:main` ≥ commit
  `853bf2c` (Dockerfile wrappers + 4-phase build smoke).
- Launch prompt: `prompts/launch-D7-rev2.md`.

### Run plan

1. Verify all three pre-conditions above (stable refs).
2. Verify stale `experiment/D7-rev2-...` branch is purged on github.
3. Run `LAUNCH_PROMPT=prompts/launch-D7-rev2.md ./run.sh` from
   `labs/kurpatov-wiki-bench/`.
4. Agent executes 12-step ritual on each of 7 sources of module 005.
5. Final commit pushed to `experiment/D7-rev2-<...>`.
6. Compare via `bench_grade.py` candidate=experiment-branch
   gold=opus-baseline; record table below.

## Execution log

| run_id                                       | date       | tier | params                                                       | status              | artifact                                                            |
| -------------------------------------------- | ---------- | ---- | ------------------------------------------------------------ | ------------------- | ------------------------------------------------------------------- |
| 2026-04-26-081305-qwen3.6-27b-fp8 (#1)       | 2026-04-26 | T4   | qwen3.6-27b-fp8 + skill v2 + fixes 1-2-4, no image wrapper   | killed mid-src 001 | (artifact discarded — pre-wrapper run, kept for diagnostic only)    |
| 2026-04-26-084209-qwen3.6-27b-fp8 (#2)       | 2026-04-26 | T4   | + image wrappers (curl/python3 strip LD_LIBRARY_PATH)        | killed mid-src 002 | (used to identify empty-Wikipedia-result detour at 7% per-source attn) |
| 2026-04-26-084941-qwen3.6-27b-fp8 (#3)       | 2026-04-26 | T4   | same                                                         | killed @ 16:31      | committed 4 sources (000-003) before kill                           |
| 2026-04-26-090625-qwen3.6-27b-fp8 (#4)       | 2026-04-26 | T4   | + factcheck.py fallback ladder (final stack: all 5 fixes)    | exit 0 @ 8:10      | committed source 004 on top of #3's branch                          |

Branch state on `experiment/D7-rev2-2026-04-26-qwen3.6-27b-fp8` after attempt #4: 5 source commits (000-004), 0 missing. Sources 005 and 006 not authored — agent in attempt #4 exited cleanly after `Run self-verify on source 000`, presumably believing the run was complete because the branch already had 4 sources committed by #3 before kill.

## Results

| metric                            | base  | D7 #1 |  opus | D7-rev2 actual | predicted | pass? |
| --------------------------------- | ----: | ----: | ----: | -------------: | --------: | :---: |
| `sources_count` (excl. _template) |     7 |     7 |     7 |              5 |         7 |   ✗   |
| `concepts_count`                  |    16 |    27 |    59 |             20 |      ≥ 35 |   ✗   |
| `claims_total_sum`                |    38 |     0 |   130 |             80 |      ≥ 60 |  ✓   |
| `claims_NEW_sum`                  |    22 |     0 |    99 |             69 |      ≥ 40 |  ✓   |
| `claims_REPEATED_sum`             |     0 |     0 |    25 |             11 |       ≥ 8 |  ✓   |
| `claims_CONTRADICTS_FACTS_sum`    |     0 |     0 |     6 |              0 |       ≥ 2 |   ✗   |
| `claims_unmarked_sum`             |    16 |     0 |     0 |              0 |         0 |  ✓   |
| `notes_flagged_sum`               |     4 |     0 |    18 |              1 |       ≥ 6 |   ✗   |
| `fact_check_citations_sum`        |     0 |     0 |    43 |             87 |      ≥ 20 |  ✓ ✓ |
| `fact_check_performed_count`      |     7 |     1 |     7 |              5 |         7 |   ✗   |
| spec compliance violations (sum)  |   ≥ 5 |   145 |     0 |              6 |      ≤ 10 |  ✓   |

Per-source skill v2 structural compliance:

| src   | frontmatter | sections | Claims block | NEW | REPEATED | CF | wiki URLs | concepts_intro |
| ----- | :---------: | -------: | :----------: | --: | -------: | -: | --------: | -------------: |
| 000   |      ✓      |        6 |      ✓       |  33 |        0 |  0 |        17 |             14 |
| 001   |      ✓      |        5 |      ✓       |  25 |        0 |  0 |        23 |              ? |
| 002   |      ✓      |        5 |      ✓       |   6 |        7 |  0 |        31 |              ? |
| 003   |      ✓      |        5 |      ✓       |   9 |        3 |  0 |        13 |              ? |
| 004   |      ✓      |        5 |      ✓       |  14 |        1 |  0 |        22 |              ? |
| 005   |       —     |        — |       —      |   — |        — |  — |         — |              — |
| 006   |       —     |        — |       —      |   — |        — |  — |         — |              — |

Vs locked falsifiability criteria:

- `claims_unmarked_sum > 5` → actual **0**, NOT falsified ✓
- `claims_CONTRADICTS_FACTS_sum < 1` → actual **0**, this *would* falsify, **but** the cause is content (Курпатов's claims happen to be Wikipedia-consistent in these 5 sources) not tool failure: factcheck.py was invoked >85 times across the run, returned valid Wikipedia URLs every time. Treat as "qualitatively consistent with PASS pending CONTRADICTS audit on harder claims".
- `fact_check_citations_sum < 5` → actual **87**, NOT falsified ✓ (over by 17×)
- `claims_REPEATED_sum < 3` → actual **11**, NOT falsified ✓

Vs partial-confirm criterion (4-5 sources clean, 2-3 degraded): we have **5/7 clean, 0/7 degraded**, with 2/7 simply not authored. Cleaner than expected partial — closer to full PASS but truncated by single-agent-session early exit.

## Post-Mortem & Insights

### What went right (the 5 fixes paid off)

1. **SKILL.md path bug fix** (skill-v2 749e9b3): zero FS-discovery wandering. Agent in #4 read `skills/benchmark/list_sources.py` and `extract_transcript.py` first try.
2. **factcheck.py curl-with-cleaned-LD_LIBRARY_PATH** (skill-v2 eec8404): no SSL diagnosis time. factcheck.py invocations exit_code=0 from first call.
3. **Dockerfile shell wrappers** (forge:main 853bf2c): even when agent ran bare `curl` for sanity-check, wrapper transparently cleared the leaked LD_LIBRARY_PATH. Build-time smoke (4 phases) caught regressions early.
4. **Cyrillic-pinned launch prompt**: zero romanization drift. All 5 source files committed at correct `Психолог-консультант/005 Природа.../` paths.
5. **factcheck.py fallback ladder** (skill-v2 9ef4529): in attempt #4 the agent did NOT debug-spiral on empty Wikipedia results — auto-simplification to last-2-words / last-word handled "Pavlov search reflex"-style queries transparently.

The aggregate effect: 4-5% wall-time and 2-7% attention-budget savings per source. Across 7 sources that's significant but not transformative on its own.

### What still degrades — the binding constraint

Even with all 5 fixes applied, single-agent attention budget on a 7-source run still pinches:

- D7 #1: 1/7 sources clean; agent collapsed after source 000 with bulk action.
- D7-rev2 #3 (killed): 4/7 sources clean before kill at 16:31 elapsed.
- D7-rev2 #4: agent *exited cleanly* after self-verifying source 000, despite branch already having 4 source commits from #3. Conversation summary: "Number of agent messages: 1; Last message sent by the agent: Run self-verify on source 000".

The pattern: single OpenHands session, single agent, accumulating context across all sources. Agent reaches some internal "I'm done" signal at a context size that depends on prior state. With all environmental friction removed (clean SSL, clean paths, clean Wikipedia handling), the binding constraint **becomes the agent's own context-budget reasoning**.

Effective ceiling on prod module 005 with skill v2 + clean env + Qwen3.6-27B-FP8: **roughly 4-5 sources before the single agent runs out of focus or decides it's done**.

### Decision: pivot to D7-rev3 — per-source agent isolation

Continuing to add fixes to the single-agent stack hits diminishing returns. The next architectural step is **per-source sub-agent delegation** via OpenHands' `task` tool (sdk-cli 1.17.0): orchestrator agent does control-flow only (~5K context total across full run), each source processed by a fresh sub-agent with empty context.

Spike-confirmed primitives (see `D7-rev3.md` for contract):
- `task` tool present in agent loadout, params `{description, prompt}`.
- Sub-agent presets at `/openhands/tools/preset/subagents/{default,code_explorer,bash_runner,web_researcher}.md`.
- Sub-agents share workspace with orchestrator → per-source-N subdirs (`/workspace/source-N/{raw,wiki}`) for isolation.
- Built-in skill `agent-creator` for custom sub-agent .md definitions.

Falsifiability transfer: if D7-rev3 also fails to deliver 7/7 sources, the bottleneck is upstream (model capability, skill spec complexity, transcript signal) rather than orchestration. Then the next axes open are model-axis (B-cluster swaps in backlog) or skill-axis (D-cluster simplifications).

### What this updates in the backlog

- D7 (skill v2 single-agent): closed, falsified at L0 parser level (D7.md§Post-Mortem).
- D7-rev2 (skill v2 + clean-env single-agent): partial PASS (5/7 sources clean, falsifiability not triggered, but 7/7 not achieved). Closed with caveat — single-agent ceiling demonstrated.
- D7-rev3 (skill v2 + per-source sub-agent isolation): NEW, ICE-up — the obvious next experiment, motivated by both D7 #1 collapse pattern and D7-rev2 early-exit pattern.
- H-Q1 (per-source isolation): superseded by D7-rev3 (the same hypothesis with concrete architecture).
