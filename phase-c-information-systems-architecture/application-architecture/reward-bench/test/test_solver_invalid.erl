%% Test fixture — Solver that returns a non-action atom.
-module(test_solver_invalid).
-export([move/1]).

move(_Board) -> 'jump'.
