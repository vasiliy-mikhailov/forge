# `src_spec_env_entity`

[`../../../../src/reward_bench/entities/env.py`](../../../../src/reward_bench/entities/env.py)
defines `Env` — the bench environment value object per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7. Frozen so a dominance comparison can run two orchestrators
against the *same* Env without mutation drift.

Fields:

    tasks_dir         Path                — where the env's task
                                            definitions live.
    canonical_scorer  CanonicalScorerPort — how a Submission body
                                            becomes a Score.
    model_client      ModelClient | None  — pre-bound LLM client for
                                            the orchestrator's agent
                                            loop. Default `None` so
                                            tests that don't need it
                                            keep their two-field
                                            constructor.

Pure value type — no IO. The seams it bundles ARE the IO; Env just
groups them so `bench(env, cfg)` and `orchestrate(env, cfg)` take
one parameter instead of many.

`frozen=True`; `eq=True` (default).
