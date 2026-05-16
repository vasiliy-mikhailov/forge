"""Cycle 109 / ADR 0018 tests: CanonicalScorerPort + FakeCanonicalScorer
+ InProcessCanonicalScorer + conftest autouse binding."""
from __future__ import annotations

import inspect

import pytest

from src.ports.canonical_scorer import CanonicalScorerPort
from src.adapters.fakes.fake_canonical_scorer import FakeCanonicalScorer
from src.tier1.entities.attempt_result import AttemptResult


# ---------------------------------------------------------------
# Port shape
# ---------------------------------------------------------------

@pytest.mark.no_fake
def test_when_canonical_scorer_port_inspected_then_has_score_method():
    """ADR 0018: CanonicalScorerPort declares `score(submission_path,
    seeds, *, hard_wall_sec, reports_root) -> AttemptResult`."""
    sig = inspect.signature(CanonicalScorerPort.score)
    params = sig.parameters
    assert "submission_path" in params
    assert "seeds" in params
    assert "hard_wall_sec" in params
    assert "reports_root" in params


# ---------------------------------------------------------------
# FakeCanonicalScorer
# ---------------------------------------------------------------

@pytest.mark.no_fake
def test_when_fake_scorer_invoked_then_records_call_and_returns_default():
    """Default-construct FakeCanonicalScorer: returns an n_games=0 default."""
    fake = FakeCanonicalScorer()
    result = fake.score("/tmp/sub.py", seeds=(1, 2, 3),
                        hard_wall_sec=42.0, reports_root="/tmp/r")
    assert isinstance(result, AttemptResult)
    assert result.n_games == 0
    assert result.hard_wall_sec == 42.0
    assert len(fake.calls) == 1
    assert fake.calls[0]["seeds"] == (1, 2, 3)
    assert fake.calls[0]["hard_wall_sec"] == 42.0


@pytest.mark.no_fake
def test_when_fake_scorer_given_script_then_returns_in_order():
    """Scripted FakeCanonicalScorer cycles through provided results."""
    r1 = AttemptResult(
        mean_score=100.0, median_score=100.0, std_score=0.0,
        max_max_tile=8, n_games=2, aggregate_walltime_sec=0.0,
        games=(), hard_wall_sec=10.0,
        stagnated_any=False, walltime_exceeded=False,
    )
    r2 = AttemptResult(
        mean_score=200.0, median_score=200.0, std_score=0.0,
        max_max_tile=16, n_games=2, aggregate_walltime_sec=0.0,
        games=(), hard_wall_sec=10.0,
        stagnated_any=False, walltime_exceeded=False,
    )
    fake = FakeCanonicalScorer(script=(r1, r2))
    out1 = fake.score("/x", seeds=(1,), hard_wall_sec=10.0)
    out2 = fake.score("/x", seeds=(2,), hard_wall_sec=10.0)
    out3 = fake.score("/x", seeds=(3,), hard_wall_sec=10.0)
    assert out1.mean_score == 100.0
    assert out2.mean_score == 200.0
    # Exhausted -> returns default empty.
    assert out3.n_games == 0


# ---------------------------------------------------------------
# DockerCanonicalScorer formally implements the Port
# ---------------------------------------------------------------

@pytest.mark.no_fake
def test_when_docker_scorer_inspected_then_implements_canonical_scorer_port():
    """ADR 0018: DockerCanonicalScorer is a CanonicalScorerPort."""
    from src.tier1.adapters.docker_canonical_scorer import DockerCanonicalScorer
    # Protocol check: any class with a matching `score` method satisfies
    # the Protocol structurally. We assert the method shape directly.
    sig = inspect.signature(DockerCanonicalScorer.score)
    params = sig.parameters
    assert "submission_path" in params
    assert "seeds" in params
    assert "hard_wall_sec" in params
    assert "reports_root" in params


# ---------------------------------------------------------------
# Conftest autouse binding: tests reaching main() WITHOUT passing
# canonical_scorer should NOT spawn Docker — they should get the Fake.
# ---------------------------------------------------------------

def test_when_main_invoked_without_explicit_scorer_then_does_not_spawn_docker(
        monkeypatch, tmp_path):
    """ADR 0018: the conftest autouse binds a FakeCanonicalScorer as
    the default in `main()` for non-live, non-no_fake tests.

    This test is NOT marked no_fake/live — it should rely on the autouse
    binding. If the binding fails, `main()` reaches the DockerCanonicalScorer
    fallback and tries to subprocess.run docker -> we'd see that call.
    """
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.frameworks import main as main_mod

    # Sentinel: if anything below tries to invoke docker via subprocess.run,
    # fail the test loudly.
    import subprocess
    real_run = subprocess.run
    def panic_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        if cmd and cmd[0] == "docker":
            pytest.fail(
                "FakeCanonicalScorer autouse binding failed — main() "
                f"spawned docker: {cmd[:3]}"
            )
        return real_run(*args, **kwargs)
    monkeypatch.setattr(subprocess, "run", panic_run)

    # Drive main(); the autouse fakes will short-circuit run_loop +
    # ensure_serving_model + canonical_scorer.
    result = main_mod.main(
        model_id="qwen3.6-27b-awq",
        config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0,
                           hard_wall_sec=10.0),
    )
    # We don't assert specific numbers — just that nothing spawned docker.
    assert result is not None
