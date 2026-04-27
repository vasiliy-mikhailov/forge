You are starting in a fresh, empty working directory inside a Linux
sandbox (Docker container). You have shell, file I/O, and HTTPS
access. Your LLM endpoint is configured for you; just call it
normally.

Model served by the inference endpoint: __INFERENCE_SERVED_NAME__
(use this verbatim as the slug for STEP 0; do NOT introspect)

Clone both repos via HTTPS using the GitHub token at the bottom of
this prompt:

  TOKEN=<see end of prompt>
  git clone https://x-access-token:$TOKEN@github.com/vasiliy-mikhailov/kurpatov-wiki-raw.git raw
  git clone https://x-access-token:$TOKEN@github.com/vasiliy-mikhailov/kurpatov-wiki-wiki.git wiki

Then read wiki/skills/benchmark/SKILL.md and execute it end-to-end.
Begin with STEP 0.

When the skill instructs `git push origin "$BRANCH"`, use the same
HTTPS+token form (the remote should already be set correctly by
the clone above).

IMPORTANT — when authoring source articles, follow the skill's
"File-writing: use the file-editor tool, not bash heredoc"
section literally. Do NOT use `python3 <<EOF` or `cat <<EOF` with
the article body inline; that pattern crashes the model's tool-call
JSON serialization on long Cyrillic strings.
