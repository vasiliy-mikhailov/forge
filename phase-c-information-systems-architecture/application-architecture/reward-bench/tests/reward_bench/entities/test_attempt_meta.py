"""AttemptMeta tests. See tests-spec/reward_bench/entities/attempt_meta/."""
from datetime import datetime, timezone

from src.reward_bench.entities.attempt_meta import AttemptMeta


def test_when_attempt_meta_constructed_then_fields_preserved():
    # Arrange
    started = datetime(2026, 5, 4, 18, 4, 23, tzinfo=timezone.utc)
    image_digest = 'sha256:' + '0' * 64
    forge_commit = '9b755cd'

    # Act
    m = AttemptMeta(
        run_id='2026-05-04-180423-qwen36-27b-fp8-tier1',
        model_id='qwen3.6-27b-fp8',
        served_model_name='qwen3.6-27b-fp8',
        task_id='2048',
        tier=1,
        started_at=started,
        image_digest=image_digest,
        forge_commit=forge_commit,
    )

    # Assert
    assert m.run_id == '2026-05-04-180423-qwen36-27b-fp8-tier1'
    assert m.model_id == 'qwen3.6-27b-fp8'
    assert m.served_model_name == 'qwen3.6-27b-fp8'
    assert m.task_id == '2048'
    assert m.tier == 1
    assert m.started_at == started
    assert m.image_digest == image_digest
    assert m.forge_commit == forge_commit
