# ADR 0009 — Per-source agent isolation via OpenHands `task` tool delegation

Status: **Proposed** (2026-04-26)
Supersedes: none
Related: [ADR 0007](0007-labs-restructure.md), [ADR 0008](0008-model-registry.md), experiments [`D7.md`](../../labs/kurpatov-wiki-bench/docs/experiments/D7.md), [`D7-rev2.md`](../../labs/kurpatov-wiki-bench/docs/experiments/D7-rev2.md), [`D7-rev3.md`](../../labs/kurpatov-wiki-bench/docs/experiments/D7-rev3.md)

## Context

The bench harness for `kurpatov-wiki-bench` runs an OpenHands agent inside a Docker container against a Russian-transcript corpus. The skill (`benchmark` v2) defines a 12-step ritual the agent applies to each source: extract transcript → pull known claims → factcheck empirical claims via Wikipedia → write a structured `source.md` with frontmatter + 5 sections + claim markers + URL citations → commit + push.

Three production runs across two experiments demonstrate a robust failure mode:

| run                              | sources clean / 7 | failure mode                                                |
| -------------------------------- | ----------------: | ----------------------------------------------------------- |
| D7 attempt #1 (skill v2 baseline)|              1/7 | bulk-action shortcut for sources 001-006 after source 000  |
| D7-rev2 attempt #3 (4 fixes)     |              4/7 | killed at 16:31 elapsed, would have likely degraded further |
| D7-rev2 attempt #4 (5 fixes)     |              5/7 | clean exit_code=0 after source 000 self-verify; agent declared task done |

The pattern across all three: a single OpenHands agent processing all 7 sources in one session accumulates context, then either degrades (loses ritual discipline mid-run) or exits early (decides the task is complete). The per-source attention budget on Qwen3.6-27B-FP8 is the binding constraint, not environment friction (D7-rev2's five environmental fixes — path bug, factcheck SSL, image wrappers, Cyrillic pin, fallback ladder — closed all known env-level distractions, yet the ceiling moved only from 1/7 to 5/7).

D7-rev2.md§Post-Mortem records the empirical ceiling: **roughly 4-5 sources before single-agent context-budget reasoning collapses**.

## Decision

**Adopt orchestrator + per-source sub-agent architecture** for the bench harness, using OpenHands SDK CLI 1.17.0's built-in `task` tool for delegation.

Concretely:

1. The bench `run.sh` invokes ONE `openhands` process. That process runs the **orchestrator** agent.
2. The orchestrator's task prompt instructs it to do *no source authoring itself*. Its job is purely:
   a. Clone the wiki + raw repos once into the shared `/workspace`.
   b. Create the experiment branch.
   c. For each source N in `[000, 001, ..., 006]`, sequentially:
      - Create per-source workdir `/workspace/source-N/`.
      - Copy or symlink `raw/` and `wiki/` clones into the workdir (or have sub-agent re-clone — see Consequences).
      - Invoke the `task` tool with a tightly-scoped sub-agent prompt: "process source N from `/workspace/source-N/wiki`, follow `skills/benchmark/SKILL.md`, return only `done` or `failed: <reason>`".
      - Wait for the sub-agent to return.
      - Run `verify-source.sh /workspace/source-N` (deterministic bash, reuses `bench_grade.py --single-source`) → JSON metrics.
      - Accumulate per-source result into orchestrator state.
      - Fail-fast if `verified=fail`: stop the run, surface to operator.
   d. After all sources processed, write `bench-report.md` from accumulated per-source JSON, commit, push.
3. Each sub-agent gets a **fresh context** (the `task` tool's contract) and a **scoped workdir** (per-source-N subdirectory of the shared workspace).
4. Sub-agent owns retry of transient failures (Wikipedia 503, network blips). Orchestrator does NOT retry — fail-fast.
5. The `task` tool's parameters (`description`, `prompt`) are the only contract surface between orchestrator and sub-agent at the agent level. The orchestrator does NOT trust sub-agent self-reports of metrics — it verifies the artifact (`source.md` on disk + commit on branch) via deterministic script.

## Consequences

### Positive

- **Per-source clean context.** Each sub-agent reads SKILL.md fresh, sees no prior-source conversational history, has no accumulated reasoning debt to draw conclusions from. This directly addresses the empirical ceiling demonstrated by D7-rev2.
- **Clean responsibility split.** Orchestrator = control flow + verification. Sub-agent = ritual on one source. Easier to debug failures (per-source events.jsonl, per-source workdir, per-source verify JSON) and easier to reason about correctness.
- **Orchestrator context stays small.** ~150-200 tokens per source (sub-agent ack + verify JSON), accumulated to ~1.5K across full run. Initial prompt + state at end of run is well below any model context limit.
- **Verifies fact, not claim.** Orchestrator decides accept/fail per-source on **what was written** (deterministic script reads the artifact), not on **what the sub-agent says it wrote** (which a hallucinating LLM might lie about).
- **Idiomatic OpenHands.** Uses `task` tool already shipped in sdk-cli 1.17.0 — no Python authoring, no harness changes beyond launch prompts and a verification script.

### Negative / costs

- **Shared workspace, not isolated container per source.** OpenHands' `task` tool delegates within the same runtime — sub-agents share the orchestrator's filesystem. Workaround is per-source-N subdirs, but this means workspace size grows linearly (7 × ~50MB = ~350MB peak from raw + wiki clones; can be wiped after each source completes if needed).
- **No parallelism in the basic design.** Sequential is the safe starting point. Parallel sub-agents would race on git push and on shared concept-index.json. A future revision could use isolated branches per-source-N and a final merge step, but that's out of scope for D7-rev3.
- **Sub-agent prompt eats orchestrator output budget.** The orchestrator must include the sub-agent's full prompt (skill v2 ritual, paths, Cyrillic pin) in *its* `task` tool call. ~2K tokens per call × 7 calls = ~14K tokens of orchestrator output budget on prompt content alone. Acceptable but not free.
- **Verification script needed.** Adds `evals/grade/verify_source.sh` (or extends `bench_grade.py` with `--single-source N --json`). Keep it small and deterministic.
- **Failure surfaces less granularly to user.** With fail-fast, a single sub-agent failure stops the whole run. Trade-off is that this gives clean signal ("source 003 failed") rather than ambiguous partial completion.

### Rejected alternatives

- **Bash-loop orchestrator** (run.sh invokes openhands 7 times sequentially, each with one source's prompt). Architecturally equivalent to the chosen design. Rejected because: (a) loses idiomatic OpenHands integration; (b) each invocation incurs full container startup overhead (~30s × 7 = ~3.5 min wasted); (c) can't naturally surface a "run-level orchestrator's view" (each invocation is independent, no cross-source state). Kept as **fallback** if the `task` tool turns out to have unexpected limitations during D7-rev3 implementation.
- **Single-agent with raised `max_iterations`** (the OpenHands per-conversation step ceiling). Rejected because the failure mode in D7-rev2 #4 was *not* hitting an iteration cap — agent decided the task was complete and called `finish`. Bigger ceiling doesn't fix premature task-completion reasoning.
- **Per-claim sub-sub-agent (tree-of-subagents)**, where each empirical claim gets its own micro-sub-agent for fact-check + dedup. Rejected at this stage as premature optimization. Revisit if D7-rev3's single-level isolation proves insufficient.

## Implementation pointers

- New launch prompts: `prompts/launch-D7-rev3-orchestrator.md` (small, control-flow-only, no skill content) and either inline sub-agent prompt or `.agents/skills/source-author.md` (full skill v2 ritual, scoped to one source).
- New script: `evals/grade/verify_source.sh` (or `bench_grade.py --single-source N --json`).
- No `run.sh` change needed beyond passing the new launch prompt via `LAUNCH_PROMPT=prompts/launch-D7-rev3-orchestrator.md`.
- Branch naming: `experiment/D7-rev3-<YYYY-MM-DD>-<served-name>`.
- Falsifiability locked in `D7-rev3.md` before run.
