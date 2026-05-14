# `test_when_execute_submission_called_then_returns_structured_observation`

Pins the [`execute_submission` tool contract](../../../../docs/adr/0008-docker-sandboxed-execute-submission-tool.md)
introduced in ADR 0008. `execute_submission` is the tier-1 ralph
loop's atomic primitive: the model emits a submission body inline,
the bench scores it on dev seeds, returns a structured JSON
observation, model iterates.

This cycle implements the dispatcher contract HOST-SIDE; the Docker
isolation per ADR 0006 layer 2 is cycle 60.

The observation is a string (the tool protocol returns text); the
string is a single-line JSON object so the model can parse it
deterministically.

Three scoped tests in this cycle:

1. **Valid Solver body** → observation JSON has `protocol_violations: []`,
   `per_seed` list with the dev seeds (1..5), each entry having
   `seed`, `score`, `max_tile`, `moves`, `state`, `walltime_sec`. The
   mean/max-tile-best fields are finite non-negative.
2. **Gym-style body (no Solver class)** → observation JSON has
   `protocol_violations` containing a string about the missing Solver
   class, AND `per_seed: []` (no games ran), `mean: 0`.
3. **Body with SyntaxError** → observation JSON has
   `protocol_violations` containing 'SyntaxError', `per_seed: []`,
   `mean: 0`. The dispatcher MUST NOT raise — it converts the failure
   into the structured observation.

The model can call execute_submission repeatedly: each call writes
the body fresh; previous body is discarded; no persistent state in
`/workspace/`.

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
