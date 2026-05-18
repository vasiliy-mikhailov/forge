# `src_spec_compose_env_spec`

[`../../../../src/reward_bench/adapters/compose_env_spec.py`](../../../../src/reward_bench/adapters/compose_env_spec.py)
is the §4 env_spec composer per
[`../../../../SOLUTION-ARCHITECTURE.md`](../../../../SOLUTION-ARCHITECTURE.md).

```python
def compose_env_spec(
    skill_md_text: str,
    env_py_path: Path,
    *,
    tier1_image: str = 'reward-bench-tier1:0.4',
    dev_games: int = 5,
    dev_seed_base: int = 2000,
    dev_timeout_sec: int = 60,
) -> str: ...
```

Pure string composition — three sections per §4: Task (the
SKILL contract verbatim), Dev test harness (executable docker
command with absolute host paths and image tag baked in), Budget
(per-dev-test wallclock hint).

Called once by `_default_env_factory` in
[`bench_main.py`](../../../../src/reward_bench/frameworks/bench_main.py)
to build the `Env.env_spec` field. The orchestrator stamps that
string into every per-iter `ContextSnapshot.env_spec`.

No IO inside the composer — file reading happens in the
env_factory before calling this.
