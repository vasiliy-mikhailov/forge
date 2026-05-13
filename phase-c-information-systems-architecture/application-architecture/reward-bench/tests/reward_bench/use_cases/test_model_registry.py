"""ModelRegistry tests. See tests-spec/reward_bench/use_cases/model_registry/."""
import pytest

from src.reward_bench.entities.model_target import ModelTarget
from src.reward_bench.use_cases.model_registry import MODEL_REGISTRY


_ALLOWED_PARSERS = frozenset({
    'qwen3_xml', 'mistral', 'gemma4', 'llama3_json', 'hermes', 'openai',
    'qwen3_coder',
})


def test_when_model_registry_inspected_then_size_matches_advertised_count():
    # Arrange (no fixtures — MODEL_REGISTRY is a module-level tuple)

    # Act
    n = len(MODEL_REGISTRY)

    # Assert
    assert n == 22, f'expected 22 entries in MODEL_REGISTRY, got {n}'


@pytest.mark.parametrize('target', MODEL_REGISTRY, ids=lambda t: t.id)
def test_when_model_registry_inspected_then_each_entry_is_a_valid_model_target(target):
    # Arrange (parametrize feeds one ModelTarget at a time)

    # Act + Assert per entry
    assert isinstance(target, ModelTarget)
    assert target.id and isinstance(target.id, str)
    assert target.hf_path and isinstance(target.hf_path, str)
    assert target.served_name and isinstance(target.served_name, str)
    assert target.tool_call_parser in _ALLOWED_PARSERS, (
        f'{target.id}: parser {target.tool_call_parser!r} '
        f'not in {sorted(_ALLOWED_PARSERS)}'
    )
    assert isinstance(target.max_model_len, int) and target.max_model_len > 0


def test_when_model_registry_inspected_then_ids_are_unique():
    # Arrange
    ids = [t.id for t in MODEL_REGISTRY]

    # Act
    n_total = len(ids)
    n_unique = len(set(ids))

    # Assert
    assert n_total == n_unique, (
        f'duplicate ids in MODEL_REGISTRY: '
        f'{sorted({i for i in ids if ids.count(i) > 1})}'
    )


def test_when_model_registry_inspected_then_lab_live_model_qwen3_6_27b_awq_present():
    # Arrange
    by_id = {t.id: t for t in MODEL_REGISTRY}

    # Act
    target = by_id.get('qwen3.6-27b-awq')

    # Assert
    assert target is not None, 'qwen3.6-27b-awq is the actually-serving lab model; must be registered'
    assert target.hf_path == 'cyankiwi/Qwen3.6-27B-AWQ-INT4'
    assert target.served_name == 'qwen3.6-27b-awq'
    assert target.max_model_len == 131072
    assert target.tool_call_parser == 'qwen3_coder'
