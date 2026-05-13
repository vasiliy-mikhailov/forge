"""CheatFinding tests. See tests-spec/reward_bench/entities/cheat_finding/."""
from src.reward_bench.entities.cheat_finding import CheatFinding


def test_when_cheat_finding_constructed_then_fields_preserved():
    # Arrange

    # Act
    f = CheatFinding(
        layer='ast',
        severity='rejected',
        rule='no_subprocess',
        line=12,
        code='import subprocess',
    )

    # Assert
    assert f.layer == 'ast'
    assert f.severity == 'rejected'
    assert f.rule == 'no_subprocess'
    assert f.line == 12
    assert f.code == 'import subprocess'
