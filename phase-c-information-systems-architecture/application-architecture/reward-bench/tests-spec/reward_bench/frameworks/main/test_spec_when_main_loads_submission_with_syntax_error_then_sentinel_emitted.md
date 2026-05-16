# `test_when_main_loads_submission_with_syntax_error_then_sentinel_emitted`

Pins ADR 0002's sentinel pattern for one more failure mode: when
the agent-loop writes a `submission.py` whose Python source is
**syntactically invalid** (e.g. the model wrote HTML or pseudocode
that doesn't compile), `main()` must emit the sentinel
`AttemptResult(n_games=0, games=())` rather than crashing.

Real-system trigger: cycle-22 live campaign with `temperature=0.7`
and `max_iters=100`. The model wrote a `submission.py` whose last
line was `</body>` — a literal HTML closing tag. `load_submission`
called `importlib`'s loader which raised `SyntaxError: invalid
syntax`. The exception propagated out of `main()` and aborted the
campaign mid-trial.

This is an extension of [ADR 0002](../../../../docs/adr/0002-main-emits-sentinel-on-malformed-submission.md):
the malformed-submission catch set now covers FileNotFoundError +
AttributeError + SyntaxError.

- **Arrange**: import `main` and `BenchConfig`. Patch
  `load_submission` (or `agent_loop.run_loop`) so that the
  submission file gets written with invalid Python source —
  simplest: monkey-patch `run_loop` to write a one-line
  `/workspace/submission.py` containing `</body>` and return.
  Also short-circuit `ensure_serving` to avoid the vLLM round-trip.
- **Act**: `result = main(model_id='qwen3.6-27b-awq',
  config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0))`.
- **Assert**:
  - `isinstance(result, AttemptResult)`.
  - `result.n_games == 0` (sentinel emitted).
  - `result.games == ()` (sentinel emitted).

Test code: [`tests/reward_bench/frameworks/test_main.py`](../../../../tests/reward_bench/frameworks/test_main.py).

## Model client injection point

- **Seam**: conftest autouse `_bind_model_client` per ADR 0014.
- **Mode**: **fake** (default) — autouse `FakeModelClient` / `FakeVllmServer`.
- **Override**: pass `model_client=` per-test, OR mark `@pytest.mark.live` / `@pytest.mark.no_fake`.

## Runtime scope

> **Runtime scope**: unit only — main() orchestration over DI seams; production-runtime coverage via canonical bench.

