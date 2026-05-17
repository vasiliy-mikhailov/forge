"""Tests for the pure helpers extracted from run_loop's state machine."""
from __future__ import annotations

from src.tier1.agent_loop_helpers import (
    promote_body_text,
    reject_finish_for_floor,
    should_smoke_stop,
    sweep_sample,
    update_best_snapshot,
)


# ---- reject_finish_for_floor ----

def test_when_finish_floor_zero_then_no_rejection():
    assert reject_finish_for_floor(0.0, None) is None
    assert reject_finish_for_floor(0.0, 5000.0) is None


def test_when_finish_floor_set_but_no_dev_runner_yet_then_rejected():
    obs = reject_finish_for_floor(100.0, None)
    assert obs is not None
    assert 'finish rejected' in obs
    assert 'unknown' in obs


def test_when_finish_floor_set_and_best_below_then_rejected():
    obs = reject_finish_for_floor(100.0, 50.0)
    assert obs is not None
    assert 'finish rejected' in obs
    assert '50' in obs
    assert '100' in obs


def test_when_finish_floor_set_and_best_above_then_no_rejection():
    assert reject_finish_for_floor(100.0, 150.0) is None


def test_when_finish_floor_set_and_best_equal_then_no_rejection():
    """Boundary: best == floor passes (>=)."""
    assert reject_finish_for_floor(100.0, 100.0) is None


# ---- update_best_snapshot ----

def test_when_no_current_best_then_new_mean_wins():
    assert update_best_snapshot(None, 50.0) == (50.0, True)


def test_when_new_mean_strictly_above_current_then_new_wins():
    assert update_best_snapshot(50.0, 100.0) == (100.0, True)


def test_when_new_mean_strictly_below_current_then_current_wins():
    assert update_best_snapshot(100.0, 50.0) == (100.0, False)


def test_when_new_mean_equals_current_then_current_wins_no_fire():
    assert update_best_snapshot(50.0, 50.0) == (50.0, False)


# ---- sweep_sample ----

def test_when_parsed_is_none_then_zero_sample():
    assert sweep_sample(5, None) == (5, 0.0, 0, 0.0)


def test_when_parsed_is_tuple_then_unpacked_sample():
    assert sweep_sample(5, (100.0, 64, 1.5)) == (5, 100.0, 64, 1.5)


# ---- should_smoke_stop ----

def test_when_smoke_off_then_no_stop_regardless():
    assert should_smoke_stop(False, 100.0) is False
    assert should_smoke_stop(False, None) is False
    assert should_smoke_stop(False, 0.0) is False


def test_when_smoke_on_but_no_dev_mean_then_no_stop():
    assert should_smoke_stop(True, None) is False


def test_when_smoke_on_but_dev_mean_zero_then_no_stop():
    assert should_smoke_stop(True, 0.0) is False


def test_when_smoke_on_and_dev_mean_positive_then_stop():
    assert should_smoke_stop(True, 100.0) is True


# ---- promote_body_text ----

def test_when_body_lacks_trailing_newline_then_one_is_appended():
    assert promote_body_text('class Solver: pass') == 'class Solver: pass\n'


def test_when_body_already_ends_with_newline_then_unchanged():
    assert promote_body_text('class Solver: pass\n') == 'class Solver: pass\n'
