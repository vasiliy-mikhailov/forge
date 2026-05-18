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


def test_when_compose_env_spec_called_then_dev_harness_streams_solver_via_heredoc_with_no_host_filesystem_writes():
    """Per §5 (no file APIs above the Runner): the dev harness
    must not mount a host-side submission.py. The Solver source
    flows via heredoc → docker stdin → cat inside the container."""
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

    # Assert — runs docker with stdin attached
    assert 'docker run' in spec
    assert ' -i ' in spec or '\\\n' in spec  # -i = attach stdin
    # heredoc carries the source code (negative on host file path)
    assert "<<'SOLVER_END'" in spec
    assert 'SOLVER_END' in spec
    assert 'cat > /workspace/submission.py' in spec
    # env.py mount stays (task runtime, not bench-agent communication)
    assert '/abs/tasks/2048/env.py:/env/env_2048.py:ro' in spec
    # but no host mount for submission.py
    assert ':/workspace/submission.py' not in spec
    assert '/tmp/sub.py' not in spec
    # image + env vars + timeout still embedded
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
