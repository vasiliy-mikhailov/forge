"""run_campaign import-resolution regression test.

See tests-spec/reward_bench/frameworks/run_campaign/."""
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / 'bin' / 'run_campaign.py'


def test_when_bin_run_campaign_executed_directly_then_imports_resolve_without_module_not_found():
    # Arrange
    assert SCRIPT.exists(), f'campaign script missing at {SCRIPT}'

    # Act
    result = subprocess.run(
        [sys.executable, str(SCRIPT), '--check'],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=30,
    )

    # Assert
    assert 'ModuleNotFoundError' not in result.stderr, (
        f'ModuleNotFoundError surfaced again — sys.path bootstrap missing?\n'
        f'stderr:\n{result.stderr}'
    )
    assert result.returncode == 0, (
        f'campaign --check exited {result.returncode}\nstderr:\n{result.stderr}'
    )
    assert 'imports OK' in result.stdout, (
        f'expected imports OK sentinel; got stdout:\n{result.stdout}'
    )
