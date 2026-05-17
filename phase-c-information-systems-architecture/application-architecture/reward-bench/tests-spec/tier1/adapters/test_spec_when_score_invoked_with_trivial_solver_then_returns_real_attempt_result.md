# `test_spec_when_score_invoked_with_trivial_solver_then_returns_real_attempt_result`
The cycle-122 live-runtime test for
[`CanonicalScorerPort`](../../../src-spec/ports/canonical_scorer/src_spec_when_canonical_scorer_score_called_then_returns_attempt_result.md)
via its production binding [`DockerCanonicalScorer`](../../../src/tier1/adapters/docker_canonical_scorer.py).
Actually invokes `docker run reward-bench-tier1:0.4` against a trivial
Solver body and asserts the returned `AttemptResult` has the expected
shape.
Pins the live-test runtime of the contract per
[AGENTS](../../../../../AGENTS.md#three-runtimes-two-scales-of-src_spec--unit--live--production).
Unit-runtime variants live in
[`test_docker_canonical_scorer.py`](../../../tests/tier1/adapters/test_docker_canonical_scorer.py)
(8 monkeypatched-subprocess tests). Production-runtime coverage is
the canonical bench itself
([`run_canonical_battery()`](../../../src/reward_bench/frameworks/run_battery.py)).
This is the test says every runtime-boundary Port MUST have.
Without it, image-missing / runner-broken / Docker-flag-wrong bugs
ship silently to the canonical bench — exactly what
demonstrated.
## Bug found at RED
Writing this test surfaced a real production bug introduced sub-A: `tasks/2048/runner_canonical.py` line 137 called
`game.step(action)` but `GameBoard` only exposes `do_action(action)`.
Image v0.4 had been carrying the buggy runner for the entire window
between and. Every canonical scoring trial's image bump emitted 20 × `walltime_exceeded` sentinels
because the in-container runner crashed with `AttributeError` before
writing `result.json` (the silent-sentinel path that
already half-fixed by adding fail-loud detection for infrastructure
errors — but `AttributeError` inside the container manifests as
returncode 1 with non-infra stderr, which correctly falls through to
the sentinel path's line between infra and
runner-crash failures).
Fix landed alongside this spec: `game.step(action)` ->
`game.do_action(action)`. Image v0.4 rebuilt.
## Contract
- **Arrange**: trivial submission body `class Solver: def move(self, board): return 'W'`
 written to `tmp_path/submission.py`. Real `DockerCanonicalScorer`
 with `env_path=tasks/2048/env.py` (no monkeypatch).
- **Act**: `scorer.score(submission_path, seeds=(1,2,3),
 hard_wall_sec=60, reports_root=tmp_path/'reports')`. Live config
 per cycle-122 LIVE_CONFIG conventions (3 seeds, 60s aggregate
 cap).
- **Assert**:
 - `result.n_games == 3`
 - every `g.final_state` in `{won, lost, max_moves, stagnated,
 walltime_exceeded, solver_error, invalid_action,
 protocol_violation}`
 - `result.mean_score >= 0.0` and not `NaN`
 - `result.max_max_tile >= 2`
 - **fewer than 3 games are `walltime_exceeded`** — this is the
 cycle-121 / cycle-123 fingerprint check that catches Docker
 infrastructure failure (image missing, daemon down, runner
 broken). If all 3 walltime_exceeded in <60s, the assert
 fails loudly with a diagnostic message.
Test code: [`../../../tests/tier1/adapters/test_docker_canonical_scorer_live.py`](../../../tests/tier1/adapters/test_docker_canonical_scorer_live.py)::`test_when_score_invoked_with_trivial_solver_then_returns_real_attempt_result`.
## Runtime injection points
| runtime | adapter binding | config |
|------------|---------------------------------------|--------------------|
| unit | `FakeCanonicalScorer` (autouse) | UNIT_CONFIG (n/a; unit tests are in `test_docker_canonical_scorer.py`) |
| **live** | `DockerCanonicalScorer(env_path=tasks/2048/env.py)` | seeds=(1,2,3), hard_wall_sec=60 |
| production | `DockerCanonicalScorer(env_path=tasks/2048/env.py)` | full battery (seeds=range(1000,1020), hard_wall_sec=300); exercised by `run_canonical_battery()` |
## Runtime scope
> **Runtime scope**: unit only — tier1 adapter contract; @live coverage at the production-scale boundary per the relevant cycle (123/124/125/128).
