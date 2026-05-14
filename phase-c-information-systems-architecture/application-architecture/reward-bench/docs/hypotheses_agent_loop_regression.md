# Hypotheses — `src/tier1/agent_loop.py` vs `src/tier1/legacy_agent_loop.py` regression

## Context

Cycle 40 ([leaderboard_data.md](../experiments/leaderboard_data.md#cycle-40-reproduction))
showed a ~40 percent score regression on qwen3.6-27b-awq under our
active `src/tier1/agent_loop.py` (peaks ~6.5k) vs the legacy
`src/tier1/legacy_agent_loop.py` (~11k single-trial best, matching
`_bak`'s 2026-05-05 baseline of 10884).

[ADR 0007](adr/0007-per-model-bench-uses-blessed-runner-until-agent-loop-bisect.md)
documents the decision to ship leaderboard data via the legacy loop
while the active loop's regression is bisected. **This file is the
bisect roadmap** — a list of candidate behaviour deltas. Each one is
a single CATS cycle (test_spec → RED test → fix → GREEN → re-bench
delta).

## Bisect order (priority desc)

| # | Hypothesis (what's missing in active `agent_loop.py`) | Test_spec name | Expected score impact |
|---|---|---|---|
| 1 | **Best-snapshot + restore**: legacy logs `[harness] new best dev MEAN=N (snapshot=True)` and copies the current `submission.py` to `submission.best.py`. At `finish` it restores `submission.best.py` over `submission.py` so scoring sees the high-water mark, not whatever the model wrote last. Our loop scores the LATEST submission. | `test_when_run_loop_observes_new_best_dev_mean_then_snapshots_submission_for_restore_at_finish` | **🔥 likely dominant — models often regress mid-trial** |
| 2 | **Finish-floor enforcement**: legacy has `--finish-floor` (default 7211 = reference_fsm baseline). If the model calls `finish` while dev MEAN < floor, the call is REJECTED and the loop keeps iterating. Our loop accepts any `finish` immediately. | `test_when_finish_called_below_finish_floor_then_rejected_and_loop_continues` | Stops early-finish at low scores |
| 3 | **max-no-improve auto-stop**: legacy counts consecutive dev_runner runs without a new best (`--max-no-improve`); on exceed, exits with `finished=True` so scoring uses the best snapshot. Our loop doesn't track this. | `test_when_dev_mean_does_not_improve_for_n_consecutive_then_loop_terminates` | Frees trial walltime; less score, more efficiency |
| 4 | **Anti-cheat refuses baseline copy**: legacy rejects `cp /tasks/2048/baselines/reference_fsm.py /workspace/submission.py` (observed firing in cycle-40 trial 1 logs). Our loop's allow-list lacks the same anti-cheat semantics around `cp`/symlink targets. | `test_when_bash_tool_attempts_baseline_copy_then_rejected_with_anti_cheat_error` | Forces original code; prevents cheaty shortcuts |
| 5 | **Best-mean tracking marker**: legacy prints `[harness] new best dev MEAN=N` AND emits `events.jsonl` row `harness/new_best_dev`. Useful for cycle-38 telemetry. | `test_when_dev_runner_output_observed_then_best_dev_mean_tracked_and_printed_via_harness_marker` | Observability only (no direct score impact) |
| 6 | **Seed param to chat completions**: legacy passes `--seed` through to vLLM's `chat/completions` `seed` param for reproducibility hint. Our loop doesn't. | `test_when_run_loop_invoked_with_seed_then_chat_completions_request_carries_seed_param` | Marginal — vLLM seed is hint, not guarantee |
| 7 | **max_tokens=12288 not 32768**: legacy caps reply at 12288 tokens. Our loop allows 32768 — model can ramble more per turn, possibly reducing turn quality. | `test_when_call_model_invoked_then_max_tokens_matches_legacy_budget` | Possibly meaningful — tighter replies = more turns per budget |
| 8 | **Context-budget pruning**: legacy has explicit `_check_context_guardrail` + pruning past 200K tokens. Our loop relies entirely on the condenser hook. Different semantics on overflow. | `test_when_messages_token_estimate_exceeds_context_budget_then_older_turns_pruned` | Marginal unless trial hits the budget |

## How to use this list

For each row (in order):

1. Open a new cycle. Create the test_spec at the named path.
2. Write a RED test in `tests/tier1/test_agent_loop.py` that reproduces
   the missing legacy behaviour against `src/tier1/agent_loop.py`.
3. Implement the fix in `src/tier1/agent_loop.py` (keep it minimal —
   one feature per cycle).
4. GREEN the test. Run TIA on the cone of influence.
5. Re-run `BENCH_MODEL_ID=qwen3.6-27b-awq pytest -m campaign
   tests/reward_bench/frameworks/campaigns/test_per_model_bak_runner.py`
   — but pointing `RUNNER` at the active `src/tier1/agent_loop.py`
   instead of legacy. The score delta vs cycle-41's 2551 is the
   evidence that this hypothesis was right.
6. Append a row to leaderboard_data.md recording the delta.

When the active loop's score reaches parity with legacy (~10k for
qwen3.6-27b-awq), ADR 0007 is superseded, `legacy_agent_loop.py` is
deleted, and this hypotheses.md file is archived.
