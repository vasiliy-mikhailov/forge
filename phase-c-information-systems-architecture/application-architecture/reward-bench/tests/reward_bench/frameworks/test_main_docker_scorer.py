"""Cycle 105 sub-C: pin main() -> DockerCanonicalScorer wiring."""
from __future__ import annotations

import inspect

import pytest

from src.tier1.entities.attempt_result import AttemptResult


@pytest.mark.no_fake
def test_when_main_signature_inspected_then_canonical_scorer_parameter_present():
    """Cycle 105 sub-C: main() gains canonical_scorer DI parameter."""
    from src.reward_bench.frameworks.main import main
    sig = inspect.signature(main)
    assert 'canonical_scorer' in sig.parameters, (
        'main() must accept canonical_scorer DI parameter'
    )
    assert sig.parameters['canonical_scorer'].default is None, (
        'canonical_scorer default must be None (production builds '
        'DockerCanonicalScorer lazily)'
    )


@pytest.mark.no_fake
def test_when_main_invoked_with_canonical_scorer_then_scorer_score_called(
        monkeypatch, tmp_path):
    """Cycle 105 sub-C: injected canonical_scorer is what's used for scoring."""
    from src.reward_bench.entities.bench_config import BenchConfig
    from src.reward_bench.frameworks import main as main_mod

    # Recorder scorer.
    calls = []
    def recorder_score(body, seeds, *, hard_wall_sec=0.0,
                       reports_root=None):
        calls.append({
            'body': body,
            'seeds': tuple(seeds),
            'hard_wall_sec': hard_wall_sec,
        })
        return AttemptResult(
            mean_score=1234.5, median_score=1000.0, std_score=42.0,
            max_max_tile=64, n_games=20, aggregate_walltime_sec=12.3,
            games=(), hard_wall_sec=hard_wall_sec,
            stagnated_any=False, walltime_exceeded=False,
        )

    class RecordingScorer:
        score_body = staticmethod(recorder_score)

    recorder = RecordingScorer()

    # Stub vLLM + run_loop + the submission write so main() reaches
    # the scorer step.
    monkeypatch.setattr(main_mod, 'ensure_serving_model',
                        lambda t: 'http://fake:8000')
    monkeypatch.setenv('VLLM_API_KEY', 'fake-key')

    def fake_run_loop(*args, **kwargs):
        ws = kwargs.get('workspace')
        # Write a minimal valid submission.py so cycle 91 grep passes.
        (ws / 'submission.py').write_text(
            'from transitions import Machine\n'
            'class Solver:\n'
            '    def __init__(self): pass\n'
            '    def move(self, b): return "W"\n'
        )
        return {'iterations': 1, 'messages': [], 'finished': True,
                'best_dev_mean': 0.0}
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)

    cfg = BenchConfig(max_iters=1, n_trials=1, temperature=0.0,
                      hard_wall_sec=300.0)
    result = main_mod.main(model_id='qwen3.6-27b-awq',
                           seeds=(1000, 1001, 1002),
                           config=cfg, canonical_scorer=recorder)

    # Scorer was called exactly once with the expected args.
    assert len(calls) == 1, f'expected 1 score() call; got {len(calls)}'
    assert calls[0]['seeds'] == (1000, 1001, 1002)
    assert calls[0]['hard_wall_sec'] == 300.0
    assert 'class Solver' in calls[0]['body']

    # main() returns the scorer's result unchanged.
    assert result.mean_score == 1234.5
    assert result.max_max_tile == 64


@pytest.mark.no_fake
def test_when_main_default_canonical_scorer_is_docker_canonical_scorer(monkeypatch):
    """Cycle 105 sub-C: when canonical_scorer is omitted, main() builds
    a DockerCanonicalScorer lazily."""
    from src.reward_bench.frameworks import main as main_mod
    from src.tier1.adapters.docker_canonical_scorer import DockerCanonicalScorer

    captured = {}
    def capture_init(self, *args, **kwargs):
        captured['constructed'] = True
        # Mark the instance with a sentinel attribute we can detect.
        self._test_sentinel = True
    monkeypatch.setattr(DockerCanonicalScorer, '__init__', capture_init)

    def capture_score(self, body, seeds, **kwargs):
        captured['scored'] = True
        return AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=0, n_games=0, aggregate_walltime_sec=0.0,
            games=(), hard_wall_sec=kwargs.get('hard_wall_sec', 0.0),
            stagnated_any=False, walltime_exceeded=False,
        )
    monkeypatch.setattr(DockerCanonicalScorer, 'score_body', capture_score)

    # Stubs.
    monkeypatch.setattr(main_mod, 'ensure_serving_model',
                        lambda t: 'http://fake:8000')
    monkeypatch.setenv('VLLM_API_KEY', 'fake-key')
    def fake_run_loop(*args, **kwargs):
        ws = kwargs.get('workspace')
        (ws / 'submission.py').write_text(
            'from transitions import Machine\n'
            'class Solver:\n'
            '    def __init__(self): pass\n'
            '    def move(self, b): return "W"\n'
        )
        return {'iterations': 1, 'messages': [], 'finished': True,
                'best_dev_mean': 0.0}
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)

    from src.reward_bench.entities.bench_config import BenchConfig
    main_mod.main(model_id='qwen3.6-27b-awq',
                  config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0,
                                     hard_wall_sec=300.0))

    assert captured.get('constructed') is True, (
        'DockerCanonicalScorer.__init__ should have been called'
    )
    assert captured.get('scored') is True, (
        'DockerCanonicalScorer.score should have been called'
    )
