# CLAUDE.md / AGENTS.md — instructions for LLM agents in this repo

Read this first if you are an LLM agent (Claude Code, Cowork, etc.)
modifying `kurpatov-wiki-bench`.

## What this repo is

The agent benchmark harness for the
[`kurpatov-wiki-wiki/skills/benchmark/SKILL.md`](https://github.com/vasiliy-mikhailov/kurpatov-wiki-wiki/blob/main/skills/benchmark/SKILL.md)
authoring task. We launch an OpenHands agent in Docker on the same
server as the vLLM endpoint, point it at that endpoint, and let it
execute the skill end-to-end. Per-run artifacts live under `runs/`.

This is **separate from forge.** forge owns vLLM serving, MLflow,
caddy, etc.; this repo is one consumer.

Full design: [`SPEC.md`](SPEC.md). Decisions: [`docs/adr/`](docs/adr/).

## First thing an agent should do

1. Read this file.
2. Read `SPEC.md` and skim `docs/adr/`.
3. Confirm `forge/inference/` is up via `make preflight` before
   running anything (this script checks `/v1/models` and asserts the
   served name matches `.env`).

## Rules for edits

- **`run.sh` is the load-bearing surface.** Most changes are there.
  Avoid splitting it into many smaller scripts unless there is a
  specific reuse driver.
- **Pin OpenHands version.** Don't `:latest`. Bumping is a
  deliberate edit, recorded in git history.
- **Do not `vllm` anything from this repo.** vLLM is owned by forge.
  If a desired model isn't loaded, instruct the operator to swap it
  there — don't reach into forge from here.
- **Don't modify `kurpatov-wiki-wiki/skills/benchmark/SKILL.md`
  from here.** That's the task definition; if it needs updates, do
  them in the wiki repo deliberately.
- **Per-run artifacts are append-only.** No run modifies another
  run's output.

## What NOT to do

- Do not bake `VLLM_API_KEY` or any secret into git-tracked files.
  `.env.example` exists for shape; `.env` is gitignored.
- Do not start a long-running service. This harness is one-shot
  per `make bench`.
- Do not try to make this work on the operator's laptop. The whole
  point of moving to OpenHands-on-server is to escape laptop
  harness flakiness; reverting that is a regression.

## Useful commands

- `make bench` — one run end-to-end.
- `make preflight` — confirm vLLM is healthy + serving the right model.
- `INFERENCE_SERVED_NAME=qwen3-32b make bench` — override per-run.
- `ls -lt runs/ | head` — most recent runs first.
- `jq '.exit_code' runs/*/summary.json` — quick exit-code overview.
