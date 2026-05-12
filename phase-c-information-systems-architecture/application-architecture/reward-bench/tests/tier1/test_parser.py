"""Tier 1 parser tests. See src-spec/tier1/src_spec_when_reply_*.md
and tests-spec/tier1/test_spec_when_reply_*.md."""
from src.tier1.parser import extract_python, has_fenced_python_block


def test_when_reply_inspected_then_contains_one_fenced_python_block(skill_tier1_reply):
    # Arrange (skill_tier1_reply fixture is a real model reply)

    # Act
    found = has_fenced_python_block(skill_tier1_reply)

    # Assert
    assert found, f'no fenced python block in reply tail: {skill_tier1_reply[-300:]!r}'


def test_when_fenced_python_extracted_then_compiles_without_syntax_error(skill_tier1_reply):
    # Arrange (skill_tier1_reply fixture is a real model reply)

    # Act
    source = extract_python(skill_tier1_reply)
    compiled = compile(source, '<solver-submission>', 'exec')

    # Assert
    assert compiled is not None
