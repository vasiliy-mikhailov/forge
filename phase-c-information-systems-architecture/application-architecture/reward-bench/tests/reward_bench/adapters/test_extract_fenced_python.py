"""extract_fenced_python helper tests."""
from __future__ import annotations


def test_when_extract_fenced_python_called_with_single_python_block_then_returns_body_without_fences():
    """§4: agent emits fenced ```python ... ``` block. Helper
    strips fence markers + language tag."""
    # Arrange
    from src.reward_bench.adapters.extract_fenced_python import (
        extract_fenced_python,
    )
    msg = (
        'Here is the solver:\n'
        '```python\n'
        'class Solver:\n'
        '    def move(self, board):\n'
        "        return 'W'\n"
        '```\n'
        'Done.'
    )

    # Act
    body = extract_fenced_python(msg)

    # Assert
    assert body == (
        'class Solver:\n'
        '    def move(self, board):\n'
        "        return 'W'\n"
    )


def test_when_extract_fenced_python_called_with_multiple_blocks_then_returns_last_block():
    """§4: agent may show iterations; the final fenced block is
    the answer."""
    # Arrange
    from src.reward_bench.adapters.extract_fenced_python import (
        extract_fenced_python,
    )
    msg = (
        'First attempt:\n'
        '```python\nFIRST\n```\n'
        'Better:\n'
        '```python\nSECOND\n```\n'
        'Final:\n'
        '```python\nTHIRD\n```\n'
    )

    # Act
    body = extract_fenced_python(msg)

    # Assert
    assert body == 'THIRD\n'


def test_when_extract_fenced_python_called_with_untagged_fence_then_treats_as_python():
    """§4: bare ``` ``` fence is accepted (some agents omit the
    language tag in final answers)."""
    # Arrange
    from src.reward_bench.adapters.extract_fenced_python import (
        extract_fenced_python,
    )
    msg = (
        'Solver:\n'
        '```\nclass Solver: pass\n```\n'
    )

    # Act
    body = extract_fenced_python(msg)

    # Assert
    assert body == 'class Solver: pass\n'


def test_when_extract_fenced_python_called_with_no_fence_then_returns_empty_string():
    """§4: absence of a fenced block → '' so the orchestrator can
    proceed (the Runner will score the empty body → 0)."""
    # Arrange
    from src.reward_bench.adapters.extract_fenced_python import (
        extract_fenced_python,
    )
    msg = 'I refuse to write code.\nIt\'s not in my training set.'

    # Act
    body = extract_fenced_python(msg)

    # Assert
    assert body == ''
