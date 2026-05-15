"""Cycle 98c / ADR 0011: contract tests for Tier1ToolRegistry adapter."""
from __future__ import annotations

from pathlib import Path

from src.adapters.tier1_tool_registry import Tier1ToolRegistry


def _ctx(workspace, env_dir, tasks_dir, *, dev_hard_wall_sec=None):
    return {
        'workspace': workspace,
        'env_dir': env_dir,
        'tasks_dir': tasks_dir,
        'dev_hard_wall_sec': dev_hard_wall_sec,
    }


# ---------------------------------------------------------------
# schemas
# ---------------------------------------------------------------

def test_when_tier1_registry_schemas_inspected_then_advertises_three_tools():
    registry = Tier1ToolRegistry()
    schemas = registry.schemas
    assert len(schemas) == 3
    names = {s['function']['name'] for s in schemas}
    assert names == {'view', 'execute_submission', 'finish'}
    for s in schemas:
        assert s['type'] == 'function'


# ---------------------------------------------------------------
# dispatch: view
# ---------------------------------------------------------------

def test_when_view_dispatched_with_valid_path_then_returns_file_contents(tmp_path):
    workspace = tmp_path / 'ws'; workspace.mkdir()
    env_dir = tmp_path / 'env'; env_dir.mkdir()
    tasks_dir = tmp_path / 'tasks'; tasks_dir.mkdir()
    (tasks_dir / 'hello.txt').write_text('hello world')

    obs = Tier1ToolRegistry().dispatch(
        'view', {'path': '/tasks/hello.txt'},
        _ctx(workspace, env_dir, tasks_dir),
    )
    assert '<view path="/tasks/hello.txt">' in obs
    assert 'hello world' in obs


def test_when_view_dispatched_with_invalid_root_then_returns_error(tmp_path):
    obs = Tier1ToolRegistry().dispatch(
        'view', {'path': '/etc/passwd'},
        _ctx(tmp_path, tmp_path, tmp_path),
    )
    assert '<error>view:' in obs
    assert '/etc/passwd' in obs


def test_when_view_dispatched_with_missing_file_then_returns_not_found(tmp_path):
    workspace = tmp_path / 'ws'; workspace.mkdir()
    obs = Tier1ToolRegistry().dispatch(
        'view', {'path': '/workspace/nope.txt'},
        _ctx(workspace, tmp_path, tmp_path),
    )
    assert 'not found' in obs


def test_when_view_dispatched_with_dotdot_escape_then_blocked(tmp_path):
    """Defence-in-depth: ../ paths must not resolve outside /tasks."""
    workspace = tmp_path / 'ws'; workspace.mkdir()
    obs = Tier1ToolRegistry().dispatch(
        'view', {'path': '/tasks/../../../etc/passwd'},
        _ctx(workspace, tmp_path, tmp_path / 'tasks'),
    )
    assert '<error>' in obs


# ---------------------------------------------------------------
# dispatch: finish
# ---------------------------------------------------------------

def test_when_finish_dispatched_then_returns_finish_signal(tmp_path):
    obs = Tier1ToolRegistry().dispatch(
        'finish', {'note': 'done'},
        _ctx(tmp_path, tmp_path, tmp_path),
    )
    assert obs == '<finish>done</finish>'


def test_when_finish_dispatched_without_note_then_empty_finish(tmp_path):
    obs = Tier1ToolRegistry().dispatch(
        'finish', {}, _ctx(tmp_path, tmp_path, tmp_path),
    )
    assert obs == '<finish></finish>'


# ---------------------------------------------------------------
# dispatch: unknown
# ---------------------------------------------------------------

def test_when_unknown_tool_dispatched_then_returns_error(tmp_path):
    obs = Tier1ToolRegistry().dispatch(
        'bash', {'cmd': 'rm -rf /'},
        _ctx(tmp_path, tmp_path, tmp_path),
    )
    assert obs == '<error>unknown tool: bash</error>'


# ---------------------------------------------------------------
# back-compat: TOOL_SCHEMAS in agent_loop.py still works
# ---------------------------------------------------------------

def test_when_agent_loop_tool_schemas_imported_then_equals_registry_schemas():
    """Cycle 98c: TOOL_SCHEMAS module-level export still resolves so
    pre-cycle-98c callers (including the _call_model shim) keep working."""
    from src.tier1.agent_loop import TOOL_SCHEMAS
    assert TOOL_SCHEMAS == Tier1ToolRegistry().schemas
