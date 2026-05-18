"""compose_env_spec helper tests."""
from __future__ import annotations


def test_when_compose_env_spec_called_then_returned_string_contains_three_sections():
    """§4 binding: env_spec is task + dev-harness + budget."""
    # Arrange
    from pathlib import Path
    from src.reward_bench.adapters.compose_env_spec import compose_env_spec

    # Act
    spec = compose_env_spec(
        skill_md_text='TASK_DESCRIPTION_SENTINEL',
        env_py_path=Path('/abs/tasks/2048/env.py'),
    )

    # Assert
    assert '# Task' in spec
    assert '# Dev test harness' in spec
    assert '# Budget' in spec


def test_when_compose_env_spec_called_with_skill_text_then_task_section_contains_it_verbatim():
    """Skill description flows through unmodified — the agent
    needs the full FSM contract text."""
    # Arrange
    from pathlib import Path
    from src.reward_bench.adapters.compose_env_spec import compose_env_spec

    # Act
    spec = compose_env_spec(
        skill_md_text='UNIQUE_TASK_BODY_42',
        env_py_path=Path('/abs/env.py'),
    )

    # Assert
    assert 'UNIQUE_TASK_BODY_42' in spec


def test_when_compose_env_spec_called_then_dev_harness_section_embeds_docker_command_with_env_path():
    """The dev-harness section is an executable docker invocation
    with the absolute host path to env.py baked in (no path
    arithmetic at agent runtime)."""
    # Arrange
    from pathlib import Path
    from src.reward_bench.adapters.compose_env_spec import compose_env_spec

    # Act
    spec = compose_env_spec(
        skill_md_text='task',
        env_py_path=Path('/abs/tasks/2048/env.py'),
        tier1_image='reward-bench-tier1:0.4',
        dev_games=5,
        dev_seed_base=2000,
        dev_timeout_sec=60,
    )

    # Assert
    assert 'docker run' in spec
    assert '/abs/tasks/2048/env.py:/env/env_2048.py:ro' in spec
    assert 'reward-bench-tier1:0.4' in spec
    assert 'REWARD_BENCH_NUM_GAMES=5' in spec
    assert 'REWARD_BENCH_SEED_BASE=2000' in spec
    assert 'timeout 60' in spec


def test_when_compose_env_spec_called_with_custom_dev_games_then_command_uses_that_count():
    """Parameters flow into the embedded command."""
    # Arrange
    from pathlib import Path
    from src.reward_bench.adapters.compose_env_spec import compose_env_spec

    # Act
    spec = compose_env_spec(
        skill_md_text='task',
        env_py_path=Path('/x'),
        dev_games=20,
    )

    # Assert
    assert 'REWARD_BENCH_NUM_GAMES=20' in spec
