# ADR 0008 — Docker-sandboxed `execute_submission` tool replaces `write_file` + `bash dev_runner`

## Status

Accepted (2026-05-14). Active. Supersedes the host-side dev_runner
contract from cycles 12-56 for tier-1 evaluation.

## Context

The current tier-1 ralph loop has the model write `submission.py`
to the host workspace via `write_file`, then optionally invoke
`bash python3 /tasks/2048/dev_runner.py /workspace/submission.py`
to score it on dev seeds. Cycle 56 measurements (and the user
observation at cycle 57 design) showed problems with this shape:

1. **The model can write any number of files under `/workspace/`** —
   helper files, its own dev_runner.py copies, its own test
   scaffolding. This proliferation distracts from the canonical
   contract (`/workspace/submission.py` is the only file scored).
2. **The model often doesn't call `dev_runner`** — it writes code
   and calls `finish` without observing the actual reward signal
   (observed in cycles 49, 51, 54, 56 active-loop campaigns).
3. **Two distinct surfaces (write_file + bash) for one logical
   action (compile + score)** — splits responsibility, makes
   feedback noisier, makes the ralph-loop unit unclear.
4. **The host-side dev_runner is not sandboxed** — it runs in the
   bench process. Per [SPEC.md](../../SPEC.md), tier-1 scoring is
   supposed to happen in a `reward-bench-tier1` Docker container
   (`--network=none`, immutable image, /env + /workspace + /reports
   mounts). Today only the FINAL scoring step uses Docker (via
   `GameBoard2048Adapter`) — the dev-runner-during-ralph-loop
   doesn't.

## Decision

Replace the current "model writes submission.py to host + bash dev_runner"
pattern with a single sandboxed tool:

    ```tool
    {"name": "execute_submission", "args": {}}
    ===FILE_BODY===
    from __future__ import annotations
    from transitions import Machine
    class Solver:
        def __init__(self): ...
        def move(self, board): return 'W'
    ```

### Tool contract

- **Input** — the model emits the FULL submission body inline (same
  fenced-body shape as today's `write_file`). No path required; the
  body IS the submission.
- **Action** — the bench:
  1. Writes the body to a transient path inside the tier-1 Docker
     image (`reward-bench-tier1:${VERSION}`).
  2. Runs the canonical `dev_runner.py` against it inside the
     container (`--network=none`, deterministic seed list).
  3. Parses dev_runner's structured output.
- **Output** — JSON observation returned to the model:
    {
      "exit_code": 0,
      "per_seed": [{"seed": 1, "score": 1024, "max_tile": 256,
                    "moves": 312, "state": "lost",
                    "walltime_sec": 0.4, "err": null}, ...],
      "mean": 870.0, "median": 928,
      "max_tile_best": 256,
      "walltime_sec_total": 2.1,
      "protocol_violations": [],
      "runtime_traceback": null
    }
- **Error shapes** — `execute_submission` NEVER raises. Failure modes
  surface in the structured output:
  - `protocol_violations: ['no Solver class', ...]` (cycle-53
    validator integrated)
  - `runtime_traceback: '...'` (per-game Solver crash)
  - `exit_code != 0` only on infrastructure errors (Docker unreachable)

### Finish-time promotion to `/workspace/submission.py`

Cycle 59 audit gap. `execute_submission` writes the body to a transient
path inside the Docker container, NOT to host `/workspace/submission.py`.
But canonical scoring (`GameBoard2048Adapter`) reads
`/workspace/submission.py` at finish time.

Resolution: the bench remembers the LAST submission body that produced
a non-error observation (any `execute_submission` call whose JSON
contained `per_seed != []`). At `finish`, the bench writes that body
to `/workspace/submission.py`. If no successful execute_submission ever
ran, an empty file is written and the canonical scoring path emits its
existing `submission protocol violation: ...` sentinel (cycle 53).

This makes the test_spec
[`test_when_run_loop_produces_submission_then_solver_move_returns_one_of_wasd`](../../tests-spec/tier1/agent_loop/test_spec_when_run_loop_produces_submission_then_solver_move_returns_one_of_wasd.md)
stay meaningful under ADR 0008 — workspace/submission.py at loop end
is exactly the model's best successful dev-time body.

### Removed surfaces (cycle 92)

- `write_file` — REMOVED from `execute_tool` dispatch and from
  SYSTEM_PROMPT. No longer accepted as a tool name.
- `bash dev_runner` — REMOVED. The host-execution path is gone;
  `execute_submission` is the only sandboxed dev-time loop.
- `ALLOWED_BASH_PREFIXES` constant removed; `subprocess` import removed
  from agent_loop.

### Final scoring is unchanged

The canonical 20-seed scoring (`score_submission` →
`GameBoard2048Adapter`) STILL runs in the same Docker tier-1
container. `execute_submission` is the dev-time feedback variant;
final scoring is the held-out variant on different seeds.

## Consequences

- **Cleaner ralph loop unit**: one tool call → one structured
  observation. Model can't proliferate auxiliary files in
  `/workspace/`.
- **Aligns with SPEC.md**: dev runs are sandboxed exactly like final
  scoring. No host execution drift.
- **Better observability**: structured per-seed output is logged in
  the trace; cycle-56's per-trial protocol-violations field becomes
  a first-class field of every dev run.
- **Migration path (completed cycle 92)**: legacy `write_file` + `bash`
  tools removed from `execute_tool` dispatch; SYSTEM_PROMPT advertises
  only `view` / `execute_submission` / `finish`. Cycle 71 confirmed
  parity (15.9k mean on Qwen3.6-27B-AWQ via `execute_submission`);
  cycle 78 smoke v2 sweep of all 22 models confirmed durability.
- **ADR 0006 layer 2 dependency**: the `reward-bench-tier1` image
  must be built and pullable. Implementation cycles will need to
  finalise the Dockerfile + immutable tag scheme already sketched in
  ADR 0006.

## Related

- [ADR 0002](0002-main-emits-sentinel-on-malformed-submission.md) —
  sentinel-on-malformed-submission. `execute_submission` carries the
  sentinel reasons into its structured output instead of needing a
  separate AttemptResult shortcut.
- [ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
  — docker tier-1 + walltime budget. `execute_submission` is the
  dev-time application of ADR 0006's runner layer.
- [ADR 0007](0007-per-model-bench-uses-blessed-runner-until-agent-loop-bisect.md)
  — blessed runner. Once `execute_submission` lands, the
  active loop should reach parity with legacy and ADR 0007 can be
  superseded.
- Task #7 in the open task list: "Wire SPEC.md Docker-sandbox:
  runner_canonical.py inside reward-bench-tier1 container" — this
  ADR is the design preamble.
