"""CheatReport tests. See tests-spec/reward_bench/entities/cheat_report/."""
from src.reward_bench.entities.cheat_finding import CheatFinding
from src.reward_bench.entities.cheat_report import CheatReport


def test_when_cheat_report_constructed_then_fields_preserved():
    # Arrange
    f1 = CheatFinding(layer='ast', severity='warning', rule='dynamic_import',
                      line=7, code='__import__(name)')
    f2 = CheatFinding(layer='bandit', severity='info', rule='B101',
                      line=42, code='assert True')

    # Act
    r = CheatReport(
        findings=(f1, f2),
        network_policy='vllm_only',
        replay_score_match=True,
        replay_tolerance_pct=5.0,
        verdict='warning',
        rejected_reason=None,
    )

    # Assert
    assert r.findings == (f1, f2)
    assert len(r.findings) == 2
    assert r.network_policy == 'vllm_only'
    assert r.replay_score_match is True
    assert r.replay_tolerance_pct == 5.0
    assert r.verdict == 'warning'
    assert r.rejected_reason is None
