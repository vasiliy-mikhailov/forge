"""End-to-end bench test. See tests-spec/reward_bench/frameworks/main/."""
import pytest
from src.reward_bench.entities.bench_config import BenchConfig
from src.tier1.entities.attempt_result import AttemptResult


# Test-friendly small config: keeps cycle wall time bounded.
_FAST = BenchConfig(max_iters=120, n_trials=1, temperature=0.0)


@pytest.mark.live
def test_when_main_invoked_with_qwen3_6_27b_awq_then_attempt_result_emitted():
    # Arrange
    from src.reward_bench.frameworks.main import main

    # Act
    result = main(model_id='qwen3.6-27b-awq', config=_FAST)

    # Assert: shape-only contract (model quality is a separate cycle)
    assert isinstance(result, AttemptResult)
    assert result.n_games == len(result.games)
    assert result.aggregate_walltime_sec >= 0.0
    if result.n_games == 20:
        # Happy path: scored 20 canonical seeds
        assert result.mean_score >= 0.0
        assert tuple(g.seed for g in result.games) == tuple(range(1000, 1020))
    else:
        # Sentinel: submission shape error
        assert result.n_games == 0
        assert len(result.games) == 0


@pytest.mark.live
def test_when_main_invoked_with_qwen3_6_27b_awq_then_solver_class_scored_20_games():
    # Arrange
    from src.reward_bench.frameworks.main import main

    # Act
    result = main(model_id='qwen3.6-27b-awq', config=_FAST)

    # Assert — strict happy-path contract (model produced valid Solver)
    assert isinstance(result, AttemptResult)
    assert result.n_games == 20, (
        f'expected 20 games scored, got {result.n_games} — sentinel emitted, '
        f'model produced wrong-shape submission'
    )
    assert len(result.games) == 20
    # Cycle 99b: 'stagnated' (cycle 78 detector) and
    # 'walltime_exceeded' (cycle 23/27 hard cap) are legitimate
    # game terminals — they prove the Solver ran without crashing.
    # The intent of this assertion is to reject Solver crashes only.
    bad = [g for g in result.games
           if g.final_state in ('solver_error', 'invalid_action')]
    assert not bad, (
        f'Solver crashes detected — model produced wrong-shape submission. '
        f'crashed game final_states: {[(g.seed, g.final_state) for g in bad]}'
    )
    assert result.mean_score >= 0.0


@pytest.mark.live
def test_when_main_invoked_with_max_iters_one_then_sentinel_emitted():
    # Arrange
    from src.reward_bench.frameworks.main import main

    # Act
    result = main(
        model_id='qwen3.6-27b-awq',
        config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0),
    )

    # Assert: max_iters=1 is too few turns to produce a valid Solver,
    # so main returns the sentinel AttemptResult.
    assert isinstance(result, AttemptResult)
    assert result.n_games == 0, (
        f'expected sentinel n_games=0 with max_iters=1, got {result.n_games}'
    )


def test_when_build_condenser_called_with_target_then_returns_llm_condenser_for_same_model_per_adr_0001():
    """Cycle 19: pin the wiring of LlmCondenser to the bench target per ADR 0001."""
    from src.reward_bench.adapters.llm_condenser import LlmCondenser
    from src.reward_bench.entities.model_target import ModelTarget
    from src.reward_bench.frameworks.main import _build_condenser

    # Arrange
    target = ModelTarget(
        id='qwen3.6-27b-awq',
        hf_path='cyankiwi/Qwen3.6-27B-AWQ-INT4',
        served_name='qwen3.6-27b-awq',
        max_model_len=131072,
        tool_call_parser='qwen3_coder',
    )

    # Act
    condenser = _build_condenser(target, 'http://stub', 'unused')

    # Assert
    assert isinstance(condenser, LlmCondenser)
    assert condenser.model_id == target.id  # per ADR 0001


def test_when_main_loads_submission_with_syntax_error_then_sentinel_emitted(monkeypatch):
    """Cycle 22.6 (no-silent-fix): real-system T=0.7 SyntaxError bug.

    Pins that main emits sentinel for syntactically invalid submission.py,
    not just for missing Solver class or missing file."""
    from src.reward_bench.frameworks import main as main_mod
    from src.tier1.entities.attempt_result import AttemptResult

    # Arrange: monkeypatch run_loop to write a syntactically invalid file
    # and short-circuit ensure_serving so we never touch vLLM.
    def fake_run_loop(*, workspace, **kwargs):
        (workspace / 'submission.py').write_text('</body>\n')

    monkeypatch.setattr(main_mod, 'ensure_serving_model',
                        lambda target: 'http://stub')
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)
    monkeypatch.setenv('VLLM_API_KEY', 'stub')

    # Act
    result = main_mod.main(
        model_id='qwen3.6-27b-awq',
        config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0),
    )

    # Assert: sentinel emitted, no crash
    assert isinstance(result, AttemptResult)
    assert result.n_games == 0
    assert result.games == ()


def test_when_main_invoked_then_config_hard_wall_sec_passed_to_score_submission(monkeypatch, tmp_path):
    """Cycle 25: pin the BenchConfig.hard_wall_sec -> score_submission wiring."""
    from src.reward_bench.frameworks import main as main_mod
    from src.tier1.entities.attempt_result import AttemptResult
    from src.tier1.entities.game_result import GameResult

    # Arrange — short-circuit serving + agent loop + adapter.
    monkeypatch.setattr(main_mod, 'ensure_serving_model',
                        lambda target: 'http://stub')
    monkeypatch.setenv('VLLM_API_KEY', 'stub')

    def fake_run_loop(*, workspace, **kwargs):
        # Write a minimal submission with a Solver class so load_submission
        # succeeds and main reaches score_submission.
        (workspace / 'submission.py').write_text(
            'from transitions import Machine\nclass Solver:\n'
            '    def move(self, board):\n'
            "        return 'W'\n"
        )
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)

    captured = {'calls': []}
    def stub_score_submission(*args, **kwargs):
        captured['calls'].append({'args': args, 'kwargs': kwargs})
        return AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=2, n_games=1, aggregate_walltime_sec=0.0,
            games=(GameResult(seed=1, score=0, max_tile=2, moves=0,
                              final_state='lost', walltime_sec=0.0),),
        )
    monkeypatch.setattr(main_mod, 'score_submission', stub_score_submission)

    # Act
    main_mod.main(
        model_id='qwen3.6-27b-awq',
        config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0,
                           hard_wall_sec=42.0),
    )

    # Assert
    assert len(captured['calls']) == 1
    assert captured['calls'][0]['kwargs'].get('hard_wall_sec') == 42.0, (
        f'hard_wall_sec not forwarded; '
        f'kwargs={captured["calls"][0]["kwargs"]}'
    )



def test_when_main_invoked_then_config_supervisor_every_k_passed_to_run_loop(monkeypatch, tmp_path):
    """Cycle 35: pin the BenchConfig.supervisor_every_k + LlmSupervisor
    -> run_loop wiring."""
    from src.reward_bench.frameworks import main as main_mod
    from src.reward_bench.use_cases.supervisor_port import SupervisorPort
    from src.tier1.entities.attempt_result import AttemptResult
    from src.tier1.entities.game_result import GameResult

    # Arrange — short-circuit serving + score_submission; recording run_loop.
    monkeypatch.setattr(main_mod, 'ensure_serving_model',
                        lambda target: 'http://stub')
    monkeypatch.setenv('VLLM_API_KEY', 'stub')

    captured = {'kwargs': None}
    def fake_run_loop(*, workspace, **kwargs):
        captured['kwargs'] = kwargs
        (workspace / 'submission.py').write_text(
            'from transitions import Machine\nclass Solver:\n'
            '    def move(self, board):\n'
            "        return 'W'\n"
        )
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)

    def stub_score_submission(*args, **kwargs):
        return AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=2, n_games=1, aggregate_walltime_sec=0.0,
            games=(GameResult(seed=1, score=0, max_tile=2, moves=0,
                              final_state='lost', walltime_sec=0.0),),
        )
    monkeypatch.setattr(main_mod, 'score_submission', stub_score_submission)

    # Act
    main_mod.main(
        model_id='qwen3.6-27b-awq',
        config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0,
                           hard_wall_sec=0.0, supervisor_every_k=7),
    )

    # Assert
    assert captured['kwargs'] is not None, 'run_loop not invoked'
    assert captured['kwargs'].get('supervisor_every_k') == 7, (
        f"supervisor_every_k not forwarded; "
        f"kwargs={captured['kwargs']}"
    )
    supervisor = captured['kwargs'].get('supervisor')
    assert supervisor is not None, 'supervisor kwarg missing'
    assert isinstance(supervisor, SupervisorPort), (
        f"supervisor does not satisfy SupervisorPort; got {type(supervisor).__name__}"
    )



def test_when_main_invoked_then_uses_ensure_serving_model_with_picked_target(monkeypatch):
    """Cycle 73: main() must wire the picked ModelTarget through to
    ensure_serving_model (cycle 42), not the legacy ensure_serving().

    Real-world repro: cycle 72 multi-model smoke. main() was calling
    ensure_serving() which hardcodes AWQ, silently overriding the
    test's ensure_serving_model(target) swap. Every smoke ran against
    AWQ regardless of parameter."""
    from src.reward_bench.frameworks import main as main_module
    from src.reward_bench.entities.bench_config import BenchConfig

    captured = {}

    def fail_legacy(*args, **kwargs):
        raise AssertionError(
            "main called the legacy ensure_serving() — should call "
            "ensure_serving_model(target) per cycle 73."
        )

    def stop_after_correct_call(target):
        captured["target"] = target
        raise RuntimeError(f"test marker — saw correct call with {target.id}")

    # If main still imports the legacy name, patch it to fail loudly.
    if hasattr(main_module, "ensure_serving"):
        monkeypatch.setattr(main_module, "ensure_serving", fail_legacy)
    # The fix: main should import ensure_serving_model and use it.
    if hasattr(main_module, "ensure_serving_model"):
        monkeypatch.setattr(main_module, "ensure_serving_model", stop_after_correct_call)
    else:
        pytest.fail(
            "main does not import ensure_serving_model yet; cycle 73 fix not in place"
        )

    with pytest.raises(RuntimeError, match="test marker"):
        main_module.main(
            model_id="qwen3.6-27b-fp8",
            config=BenchConfig(max_iters=1, n_trials=1, hard_wall_sec=60.0),
        )

    assert "target" in captured, "ensure_serving_model was never called"
    target = captured["target"]
    assert target.id == "qwen3.6-27b-fp8", target.id
    assert target.served_name == "qwen3.6-27b-fp8", target.served_name
    assert target.hf_path == "Qwen/Qwen3.6-27B-FP8", target.hf_path


def test_when_main_completes_then_attempt_result_best_dev_mean_matches_run_loop_return(monkeypatch, tmp_path):
    """Cycle 79 / ADR 0009 v3: main passes run_loop's best_dev_mean
    through into AttemptResult.

    Mocks ensure_serving_model, run_loop, and score_submission so the
    test is a pure wiring check (not an integration test)."""
    from src.reward_bench.frameworks import main as main_mod
    from src.tier1.entities.attempt_result import AttemptResult as AR

    monkeypatch.setattr(main_mod, 'ensure_serving_model', lambda target: 'http://stub')
    monkeypatch.setenv('VLLM_API_KEY', 'stub')

    def fake_run_loop(*, workspace, **kwargs):
        (workspace / 'submission.py').write_text(
            'from transitions import Machine\nclass Solver:\n'
            '    def __init__(self): pass\n'
            "    def move(self, board): return 'S'\n"
        )
        return {
            'iterations': 5,
            'messages': [],
            'finished': True,
            'best_dev_mean': 1234.5,
        }
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)

    # Mock score_submission so the test doesn't actually play games.
    def fake_score(*args, **kwargs):
        return AR(
            mean_score=42.0, median_score=42.0, std_score=0.0,
            max_max_tile=16, n_games=20, aggregate_walltime_sec=0.1,
        )
    monkeypatch.setattr(main_mod, 'score_submission', fake_score)

    result = main_mod.main(
        model_id='qwen3.6-27b-awq',
        config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0),
    )

    assert isinstance(result, AR)
    assert result.best_dev_mean == 1234.5, (
        f'expected best_dev_mean=1234.5; got {result.best_dev_mean}'
    )
    assert result.mean_score == 42.0  # informational; not the smoke signal


def test_when_main_invoked_in_smoke_mode_with_positive_dev_mean_then_skips_canonical_scoring(monkeypatch, tmp_path):
    """Cycle 80 / ADR 0009 v3: in smoke mode (config.smoke_early_stop=True)
    with run_loop returning best_dev_mean > 0, main() skips
    score_submission entirely."""
    from src.reward_bench.frameworks import main as main_mod
    from src.tier1.entities.attempt_result import AttemptResult as AR

    monkeypatch.setattr(main_mod, 'ensure_serving_model', lambda target: 'http://stub')
    monkeypatch.setenv('VLLM_API_KEY', 'stub')

    def fake_run_loop(*, workspace, **kwargs):
        (workspace / 'submission.py').write_text(
            'from transitions import Machine\nclass Solver:\n'
            '    def __init__(self): pass\n'
            "    def move(self, board): return 'S'\n"
        )
        return {
            'iterations': 14, 'messages': [], 'finished': True,
            'best_dev_mean': 42.0,
        }
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)

    score_calls = {'n': 0}
    def fake_score(*a, **kw):
        score_calls['n'] += 1
        return AR(mean_score=999, median_score=999, std_score=0,
                  max_max_tile=0, n_games=0, aggregate_walltime_sec=0)
    monkeypatch.setattr(main_mod, 'score_submission', fake_score)

    result = main_mod.main(
        model_id='qwen3.6-27b-awq',
        config=BenchConfig(max_iters=1, n_trials=1, temperature=0.0,
                          smoke_early_stop=True),
    )

    assert score_calls['n'] == 0, (
        f'score_submission was called {score_calls["n"]} times in '
        f'smoke mode after positive dev_mean; expected 0 calls'
    )
    assert result.best_dev_mean == 42.0
    assert result.mean_score == 0.0
    assert result.n_games == 0



def test_when_main_invoked_with_nonzero_hard_wall_sec_then_run_loop_receives_scaled_dev_budget(
        monkeypatch, tmp_path):
    """Cycle 77 / ADR 0006: main() derives
    dev_hard_wall_sec = config.hard_wall_sec * 5 / len(seeds)
    and threads it into run_loop. Pins the wiring."""
    from src.reward_bench.frameworks import main as main_mod

    captured = {}
    def fake_run_loop(**kwargs):
        captured.update(kwargs)
        return {'iterations': 0, 'messages': [],
                'finished': True, 'best_dev_mean': 0.0}
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)
    monkeypatch.setattr(main_mod, 'ensure_serving_model', lambda t: 'http://stub')
    monkeypatch.setenv('VLLM_API_KEY', 'stub')

    # Stub the canonical scorer so main() returns quickly.
    from src.tier1.entities.attempt_result import AttemptResult
    def fake_score_submission(**kwargs):
        return AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=0, n_games=20, aggregate_walltime_sec=0.0,
            games=(), hard_wall_sec=kwargs.get('hard_wall_sec', 0.0),
            stagnated_any=False, walltime_exceeded=False,
        )
    monkeypatch.setattr(main_mod, 'score_submission', fake_score_submission)

    # Canonical = 60s / 20 seeds; dev should derive 60 * 5/20 = 15.0.
    main_mod.main(
        model_id='qwen3.6-27b-awq',
        seeds=range(1000, 1020),
        config=BenchConfig(max_iters=1, n_trials=1, hard_wall_sec=60.0),
    )

    assert captured.get('dev_hard_wall_sec') == 15.0, (
        f'expected dev_hard_wall_sec=15.0 (=60*5/20); '
        f'got {captured.get("dev_hard_wall_sec")}'
    )


def test_when_main_invoked_with_zero_hard_wall_sec_then_run_loop_dev_budget_is_none(
        monkeypatch, tmp_path):
    """Cycle 77: when canonical aggregate cap is disabled (=0, ADR 0003
    default), main() passes dev_hard_wall_sec=None so the dev path uses
    the cycle-70 module default DEV_HARD_WALL_S (30s)."""
    from src.reward_bench.frameworks import main as main_mod

    captured = {}
    def fake_run_loop(**kwargs):
        captured.update(kwargs)
        return {'iterations': 0, 'messages': [],
                'finished': True, 'best_dev_mean': 0.0}
    monkeypatch.setattr(main_mod, 'run_loop', fake_run_loop)
    monkeypatch.setattr(main_mod, 'ensure_serving_model', lambda t: 'http://stub')
    monkeypatch.setenv('VLLM_API_KEY', 'stub')

    from src.tier1.entities.attempt_result import AttemptResult
    monkeypatch.setattr(
        main_mod, 'score_submission',
        lambda **k: AttemptResult(
            mean_score=0.0, median_score=0.0, std_score=0.0,
            max_max_tile=0, n_games=20, aggregate_walltime_sec=0.0,
            games=(), hard_wall_sec=0.0,
            stagnated_any=False, walltime_exceeded=False,
        ),
    )

    main_mod.main(
        model_id='qwen3.6-27b-awq',
        config=BenchConfig(max_iters=1, n_trials=1, hard_wall_sec=0.0),
    )

    assert captured.get('dev_hard_wall_sec') is None, (
        f'expected None (-> module default); '
        f'got {captured.get("dev_hard_wall_sec")}'
    )
