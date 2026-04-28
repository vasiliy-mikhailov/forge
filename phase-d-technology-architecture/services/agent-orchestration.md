# Service: Agent orchestration & sub-agent delegation

- **Component:** OpenHands SDK 1.17.0 + TaskToolSet, file-based
  sub-agent definitions.
- **Lab:** [`wiki-bench/orchestrator/`](../../phase-c-information-systems-architecture/application-architecture/wiki-bench/orchestrator/).

## Quality dimensions and trajectories

- **Top-orch context bound** — L1: Python-loop driver creates fresh
  `Conversation` per source (Invariant A); top-orch input bounded.
  But 0 % KV-cache reuse across sub-agent delegations within a
  Conversation, so each call re-prefills its system prompt.
  L2: KV-cache reuse across same-Conversation sub-agent calls
  (vLLM prefix-cache + openhands integration). Estimated impact:
  ~5-10× fewer prefill tokens per source, ~3-4 min saved per
  source on a 7-source run.

## Invariants (this service)

- **Invariant A (per-source top-orch isolation).** Production drivers
  must instantiate a fresh `Conversation(...)` per source inside a
  Python `for` loop. Long-lived
  `conv.send_message(master_for_all_sources)` followed by single
  `conv.run()` is the anti-pattern. Bench's
  `orchestrator/run-d8-pilot.py` is the canonical realisation.
