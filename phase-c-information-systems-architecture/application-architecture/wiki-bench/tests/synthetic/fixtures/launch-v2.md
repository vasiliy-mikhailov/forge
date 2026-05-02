You are starting in a sandboxed Linux container. Two working trees are
pre-mounted; do not clone anything.

- `/workspace/raw` — input transcripts (already a git repo)
- `/workspace/wiki` — output workspace (already a git repo, local only)

Your LLM endpoint is configured via env vars; just call it normally.
Model served by the inference endpoint: __SERVED__

Read `/workspace/wiki/skills/synth-benchmark/SKILL.md` and execute it
end-to-end. The skill processes FOUR pre-staged synthetic sources
(`001 Парето и Мур`, `002 Парето и Эверест`, `003 Мур и Сатурн`,
`004 Эверест и Пи`) and writes source articles + commits locally.

The v2 skill mandates two helper-script tools:
  - skills/synth-benchmark/scripts/get_known_claims.py  (REPEATED detection)
  - skills/synth-benchmark/scripts/factcheck.py "<claim>"  (fact-check)

These are not optional — the skill explicitly requires their use, and
URL citations must come from factcheck.py output.

Do NOT push to any remote. This is a sandboxed test against
synthetic data.

Begin.


**Transitive coverage** (per [ADR 0013 dec 9](../../../../phase-preliminary/adr/0013-md-as-source-code-tdd.md)
+ [ADR 0017](../../../../phase-preliminary/adr/0017-motivation-spans-all-layers.md)):
measurable motivation chain inherited from the lab's AGENTS.md.
