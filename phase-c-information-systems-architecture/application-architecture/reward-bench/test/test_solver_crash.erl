%% Test fixture — Solver that crashes.
-module(test_solver_crash).
-export([move/1]).

move(_Board) -> error(boom).
