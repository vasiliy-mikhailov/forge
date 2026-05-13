# `src_spec_when_bash_tool_executed_with_allowed_cmd_then_returns_stdout`

`execute_tool('bash', args, ...)` runs `args['cmd']` via
`subprocess.run` and returns:

    <bash exit={code}>
    --- stdout ---
    {stdout}
    --- stderr ---
    {stderr}
    </bash>

Constraints (lifted from `_bak/bin/agent_loop.py:49-59` and `132-154`):

- The command MUST start with one of the prefixes in
  `ALLOWED_BASH_PREFIXES` (verbatim from `_bak`: `python3 /tasks/2048/dev_runner.py /workspace/submission.py`,
  `ls /workspace`, `ls /tasks`, `ls /env`, `cat /workspace/submission.py`,
  `head /workspace/submission.py`, `cat /tasks/2048/SKILL_tier1.md`,
  `cat /env/env_2048.py`, plus a `python` variant of dev_runner).
- Virtual paths `/workspace`, `/tasks`, `/env` inside the command are
  translated to their host equivalents before exec.
- 120 s timeout per call (lifted from _bak).
- `PYTHONPATH` includes `env_dir` so dev_runner's `import env_2048`
  resolves.

This cycle pins only the happy-path stdout case. Disallowed-command
and timeout error paths land in their own cycles when needed.
