You are starting in a fresh, empty working directory inside a Linux sandbox (Docker container). You have shell, file I/O, and HTTPS access. Your LLM endpoint is configured for you; just call it normally.

Model served by the inference endpoint: __INFERENCE_SERVED_NAME__ (use this verbatim as the slug for STEP 0; do NOT introspect)

This is **experiment D7** — skill v2 tool-driven (12-step ritual + helper scripts). The skill v2 lives on a feature branch `skill-v2` of `kurpatov-wiki-wiki`.

Clone both repos via HTTPS using the GitHub token at the bottom of this prompt:

```
TOKEN=<see end of prompt>
git clone https://x-access-token:$TOKEN@github.com/vasiliy-mikhailov/kurpatov-wiki-raw.git raw
git clone https://x-access-token:$TOKEN@github.com/vasiliy-mikhailov/kurpatov-wiki-wiki.git wiki

# IMPORTANT: switch to skill-v2 branch — it has the v2 skill + helper scripts.
cd wiki && git checkout skill-v2 && git pull --ff-only && cd ..
```

Then read `wiki/skills/benchmark/SKILL.md` (which is now the v2 ritual) and execute it end-to-end. Begin with STEP 0.

When the skill instructs `git push origin "$BRANCH"`, use the same HTTPS+token form (the remote should already be set correctly by the clone above). Branch name format for this experiment is `experiment/D7-<YYYY-MM-DD>-<served-name>` (note the `experiment/` prefix instead of `bench/`).

Two helper scripts are mandatory contracts in v2 and live at `wiki/skills/benchmark/scripts/`:
- `get_known_claims.py` — required call per source for REPEATED detection
- `factcheck.py "<claim>"` — required call per empirical claim for fact-check + URL citations

Their absence means you cannot complete the source — surface to operator.
