# `src_spec_when_skill_tier1_prompt_sent_then_reply_completes_within_5_min`

For the static-submission protocol, the model accepts the entire
`tasks/2048/SKILL_tier1.md` content as the user prompt, runs at
`max_tokens=32768`, `temperature=0.0`, and returns a non-empty
content string within 300 s of wall-clock time.

The 300 s budget is the upper bound for a useful per-attempt
inference cost. Models that exceed it are not viable for the
Tier-1 bench in this configuration.

No bench-side implementation in `src/` yet; downstream cycles
(L3.2 and later) will introduce the extractor and harness that
consume this reply.
