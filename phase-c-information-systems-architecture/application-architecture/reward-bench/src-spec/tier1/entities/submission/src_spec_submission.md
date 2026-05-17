# `src_spec_submission_entity`

`src.tier1.entities.submission.Submission` is a frozen `dataclass`
holding what the per-iter orchestrator returns to the main process:
the candidate submission body, its canonical score, and the wall
time the iter consumed. Pure domain type — no IO, no HTTP, no
external systems.

Fields (aligning with
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md)
§7 `bench :: Env -> BenchConfig -> Submission`):

    body          str    — the solver source the iter produced.
    score         float  — canonical score of `body` under the env.
    walltime_sec  float  — wall time the iter took to produce `body`.

Allowed imports (kept minimal to satisfy the entities-purity rule):

    dataclasses

The dataclass is `frozen=True` so instances are hashable / immutable
value objects — matches the Senior Haskell AI Engineer stance
(immutability over mutation) and the §7 framing that a submission
is what survives the subagent's context death.

Source: [`../../../../src/tier1/entities/submission.py`](../../../../src/tier1/entities/submission.py).
