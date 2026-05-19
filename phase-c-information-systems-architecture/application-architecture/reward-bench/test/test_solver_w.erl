%% Test fixture — Solver that always returns the same direction.
%% Used in runner_canonical_tests.erl.
-module(test_solver_w).
-export([move/1]).

move(_Board) -> w.
