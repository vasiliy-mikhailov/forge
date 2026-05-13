"""ModelTarget entity tests. See tests-spec/reward_bench/entities/model_target/."""
from src.reward_bench.entities.model_target import ModelTarget


def test_when_mistral_small_3_2_24b_model_target_constructed_then_fields_match_registry():
    # Arrange (registry source: wiki-compiler/configs/models.yml entry mistral-small-3.2-24b)

    # Act
    target = ModelTarget(
        id='mistral-small-3.2-24b',
        hf_path='RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4',
        served_name='mistral-small-3.2-24b',
        max_model_len=131072,
        tool_call_parser='mistral',
    )

    # Assert
    assert target.id == 'mistral-small-3.2-24b'
    assert target.hf_path == 'RedHatAI/Mistral-Small-3.2-24B-Instruct-2506-NVFP4'
    assert target.served_name == 'mistral-small-3.2-24b'
    assert target.max_model_len == 131072
    assert target.tool_call_parser == 'mistral'
