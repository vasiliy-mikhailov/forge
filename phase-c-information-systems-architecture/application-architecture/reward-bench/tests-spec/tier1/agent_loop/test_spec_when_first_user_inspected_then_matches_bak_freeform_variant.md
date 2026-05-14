# `test_when_first_user_inspected_then_matches_bak_freeform_variant`

Regression test pinning [`FIRST_USER`](../../../../src/tier1/agent_loop.py)
to the freeform variant from `_bak/bin/agent_loop.py`. Required after
the cycle-39 discovery that the over-prescriptive variant (with
inline `from transitions import Machine` stub + "DO NOT skip
transitions" directives) caused the qwen3.6-27b-awq model to write
phantom-trigger code (e.g. `self.machine.start()`,
`self.machine.to_opening()`) that crashed at runtime.

`_bak`'s `2026-05-05-qwen3.6-27b-awq-int4-tier1` reports-stage2
artifact (the same model, same canonical seeds 1000-1019) scored
mean=10884, max=21208 with two seeds winning at 2048 tile. Our
cycle-36 with the over-prescribed variant peaked at mean=6261. The
delta is attributable solely to FIRST_USER.

Test asserts the literal FIRST_USER string. Future cycles that want
to change FIRST_USER MUST update the pinned text here AND record
the leaderboard data point under the new prompt — making prompt
changes test-spec-backed per cats.md artifacts-come-from-tests.

- **Arrange**: import `FIRST_USER` from `src.tier1.agent_loop`.
- **Act**: read its value.
- **Assert**: it equals the `_bak` literal — one short paragraph,
  no code stubs, no library mandates, just "Read the spec, write
  your submission, iterate."

Test code: [`tests/tier1/test_agent_loop.py`](../../../../tests/tier1/test_agent_loop.py).
