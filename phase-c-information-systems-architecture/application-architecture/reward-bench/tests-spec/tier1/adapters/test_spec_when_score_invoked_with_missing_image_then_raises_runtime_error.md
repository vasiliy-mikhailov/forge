# `test_spec_when_score_invoked_with_missing_image_then_raises_runtime_error`
Pins the cycle-121 fix: `DockerCanonicalScorer.score()` MUST raise
`RuntimeError` (with informative `stderr` content) when `docker run`
fails with returncode 125 and stderr indicates the image is missing
(`Unable to find image... locally`, `No such image`,
`manifest unknown`, `pull access denied`).
Pre-cycle-121 behaviour: the scorer caught the failure path through
`if not result_path.exists()` and emitted 20×`walltime_exceeded`
sentinels — silently producing zero-score artifacts that look like
"slow solver hit timeout" but are actually "infrastructure broken."
This wasted compute and polluted the canonical battery for the
4 hours between the cycle-105 image bump and the user's CPU-load
observation.
The contract per
[SOLUTION-ARCHITECTURE](../../../SOLUTION-ARCHITECTURE.md)
and the [CanonicalScorerPort src_spec](../../../src-spec/ports/canonical_scorer/src_spec_when_canonical_scorer_score_called_then_returns_attempt_result.md):
 > **MAY raise on infrastructure failure** (Docker unavailable, image
 > missing, disk full). Those are bench bugs, not submission bugs,
 > and shouldn't be silently turned into `solver_error`.
## Contract
- **Arrange**: build a `DockerCanonicalScorer` with `cpus=2` (avoid
 host-cpu probe) and `env_path=None`. Monkeypatch `subprocess.run`
 to return a `CompletedProcess` with `returncode=125`,
 `stdout=""`, `stderr="Unable to find image 'reward-bench-tier1:9.9'
 locally\ndocker: Error response from daemon:..."`.
- **Act**: call `scorer.score(submission_path=<tmp>, seeds=(1,2,3))`.
- **Assert**: `pytest.raises(RuntimeError)` matches; the exception
 message includes the stderr content for diagnosis. NO
 `AttemptResult` is returned. NO sentinel `walltime_exceeded` games
 are produced.
Test code: [`../../../tests/tier1/adapters/test_docker_scorer_infra_failure.py`](../../../tests/tier1/adapters/test_docker_scorer_infra_failure.py)::`test_when_score_invoked_with_missing_image_then_raises_runtime_error`.
## Model client injection point
- **Seam**: monkeypatch `subprocess.run` directly (the scorer holds
 no DI seam for subprocess; that's a separate future cycle).
- **Mode**: `no_fake` — exercises real bench seam offline.
## Companion contract — container-crashed-mid-run
`test_when_score_invoked_with_runtime_failure_then_sentinels_per_seed`:
when subprocess returns `returncode != 0` but stderr does NOT match
any infrastructure-failure pattern (i.e., the runner started and
crashed during scoring), the scorer continues to emit
`walltime_exceeded` sentinels as before. This pins the line between
"raise on infra" and "sentinel on runner-crash" so a future
overcorrection doesn't make the scorer raise on legitimate solver
failures.
## Runtime scope
> **Runtime scope**: unit only — tier1 adapter contract; @live coverage at the production-scale boundary per the relevant cycle (123/124/125/128).
