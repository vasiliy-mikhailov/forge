# ADR 0008 — Docker-sandboxed `execute_submission` tool replaces `write_file` + `bash dev_runner`

## Status

Accepted (2026-05-14). Active. Supersedes the host-side dev_runner
contract from cycles 12-56 for tier-1 evaluation.

## Context

The current tier-1 ralph loop has the model `write_file` a
`submission.py` to host workspace, then optionally `bash python3
/tasks/2048/dev_runner.py /workspace/submission.py`. Problems:

1. **File proliferation.** The model writes helpers, its own dev_runner
   copies, test scaffolding under `/workspace/`. Only `submission.py`
   is scored.
2. **`dev_runner` often skipped.** Model writes code and calls `finish`
   without observing the reward signal.
3. **Two surfaces for one action.** `write_file` + `bash` split a
   compile-and-score responsibility.
4. **Host-side dev_runner not sandboxed.** Per [SPEC.md](../../SPEC.md),
   tier-1 scoring runs in a `reward-bench-tier1` container
   (`--network=none`). Today only FINAL scoring uses Docker; the
   in-loop dev runner does not.

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

`execute_submission` writes to a transient path inside the container,
not host `/workspace/submission.py`. Canonical scoring reads the host
path. Resolution: the bench remembers the LAST body that produced a
non-error observation (`per_seed != []`) and writes it to
`/workspace/submission.py` at `finish`. If none succeeded, an empty
file triggers the existing `submission protocol violation` sentinel.

### Removed surfaces

- `write_file` — REMOVED from dispatch and SYSTEM_PROMPT.
- `bash dev_runner` — REMOVED. `execute_submission` is the only
  dev-time loop. `ALLOWED_BASH_PREFIXES` and `subprocess` removed.

### Final scoring is unchanged

Canonical 20-seed scoring still runs in the tier-1 container.
`execute_submission` is dev-time; final scoring is held-out seeds.

## Consequences

- **Cleaner ralph loop unit.** One tool call -> one structured
  observation. No file proliferation.
- **Aligns with SPEC.md.** Dev runs sandboxed like final scoring.
- **Better observability.** Per-seed output logged; protocol-violations
  is a first-class field.
- **Migration complete.** SYSTEM_PROMPT advertises only
  `view` / `execute_submission` / `finish`. Parity verified at 15.9 k
  on Qwen3.6-27B-AWQ.
- **ADR 0006 layer 2 dependency.** `reward-bench-tier1` image must be
  built and tagged.

## Related

- [ADR 0002](0002-main-emits-sentinel-on-malformed-submission.md) —
  `execute_submission` carries sentinel reasons in its output.
- [ADR 0006](0006-sandboxed-scoring-docker-tier1-and-walltime-budget.md)
  — dev-time application of the runner layer.
