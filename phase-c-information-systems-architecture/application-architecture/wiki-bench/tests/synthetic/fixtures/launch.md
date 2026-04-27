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
