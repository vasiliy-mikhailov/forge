You are starting in a sandboxed Linux container. Two working trees are
pre-mounted; do not clone anything.

- `/workspace/raw` — input transcripts (already a git repo at HEAD)
- `/workspace/wiki` — output workspace (already a git repo at HEAD)

Your LLM endpoint is configured via env vars; just call it normally.

Model served by the inference endpoint: __SERVED__

Read `/workspace/wiki/skills/synth-benchmark/SKILL.md` and execute it
end-to-end. The skill processes two pre-staged synthetic sources
(`001 Парето и Мур` and `002 Парето и Эверест`) and writes source
articles + commits locally.

Do NOT push to any remote. This is a sandboxed test against
synthetic data. There is no remote configured.

Begin.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
motivation chain inherited from the lab's AGENTS.md.
