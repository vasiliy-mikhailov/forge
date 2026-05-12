"""Tier 1 harness tests. See src-spec/tier1/src_spec_when_extracted_module_*.md
and tests-spec/tier1/test_spec_when_extracted_module_*.md."""
import inspect
import tempfile
from pathlib import Path

from src.tier1.harness import load_submission
from src.tier1.parser import extract_python


def _write_submission(skill_tier1_reply):
    source = extract_python(skill_tier1_reply)
    f = tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False)
    f.write(source)
    f.close()
    return Path(f.name)


def test_when_extracted_module_loaded_then_exposes_class_solver(skill_tier1_reply):
    # Arrange
    submission = _write_submission(skill_tier1_reply)

    # Act
    module = load_submission(submission)

    # Assert
    assert hasattr(module, 'Solver'), 'submission has no Solver attribute'
    assert inspect.isclass(module.Solver), 'Solver is not a class'
