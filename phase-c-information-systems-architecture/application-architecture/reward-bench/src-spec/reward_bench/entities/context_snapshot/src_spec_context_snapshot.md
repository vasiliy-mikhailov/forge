# `src_spec_context_snapshot`

[`../../../../src/reward_bench/entities/context_snapshot.py`](../../../../src/reward_bench/entities/context_snapshot.py)
defines `ContextSnapshot` — what the `SolutionGenerator` receives
per iter, per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§2.

Fields:

    env_spec             str                       — rendered task contract
    best_so_far          Submission                — running best body+score
    history_digest       tuple[Submission, ...]    — prior iters' submissions
    iters_remaining      int                       — iters orchestrator will run
    time_remaining_sec   float                     — wallclock budget left
    budget_sec_per_seed  float                     — dev scorer per-seed cap

Frozen value type. The SolutionGenerator's deliberation tokens die
with its context each iter; this snapshot is the only state that
survives.
