"""End-to-end bench test. See tests-spec/reward_bench/frameworks/main/."""
from src.reward_bench.entities.bench_config import BenchConfig
from src.tier1.entities.attempt_result import AttemptResult


# Test-friendly small config: keeps cycle wall time bounded.
_FAST = BenchConfig(max_iters=30, n_trials=1, temperature=0.0)


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
    bad = [g for g in result.games
           if g.final_state not in ('won', 'lost')]
    assert not bad, f'unexpected final_states: {[g.final_state for g in bad]}'
    assert result.mean_score >= 0.0


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

    monkeypatch.setattr(main_mod, 'ensure_serving',
                        lambda: 'http://stub')
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
