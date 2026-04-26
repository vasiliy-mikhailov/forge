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

| run_id                                       | date       | tier | params                                                    | status    | artifact                                                       |
| -------------------------------------------- | ---------- | ---- | --------------------------------------------------------- | --------- | -------------------------------------------------------------- |
| (pending)                                    | 2026-04-26 | T4   | qwen3.6-27b-fp8 + skill v2 + clean-env, module 005, 7 src | _pending_ | branch `experiment/D7-rev2-2026-04-26-qwen3.6-27b-fp8`         |

## Results (filled after run)

_Pending — will record bench-grade table + diff against base/D7-#1/opus
columns above._

## Post-Mortem & Insights

_Pending._
