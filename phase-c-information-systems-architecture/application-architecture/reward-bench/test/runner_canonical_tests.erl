%% @doc EUnit suite for runner_canonical.
-module(runner_canonical_tests).
-include_lib("eunit/include/eunit.hrl").
-include("records.hrl").

trivial_w_solver_plays_until_lost_test() ->
    R = runner_canonical:play_game(test_solver_w, 42, 5.0, 500),
    ?assert(R#game_result.state =:= lost
            orelse R#game_result.state =:= max_moves_reached),
    ?assert(R#game_result.moves > 0),
    ?assert(R#game_result.score >= 0),
    ?assert(R#game_result.walltime_sec >= 0.0).

crashing_solver_yields_state_error_test() ->
    R = runner_canonical:play_game(test_solver_crash, 42, 5.0, 100),
    ?assertEqual(error, R#game_result.state),
    ?assertEqual({error, boom}, R#game_result.error),
    %% Crashed on move 1 — env never advanced.
    ?assertEqual(0, R#game_result.moves).

invalid_action_yields_state_error_test() ->
    R = runner_canonical:play_game(test_solver_invalid, 42, 5.0, 100),
    ?assertEqual(error, R#game_result.state),
    ?assertEqual({invalid_action, jump}, R#game_result.error).

nonexistent_module_yields_state_error_test() ->
    R = runner_canonical:play_game(no_such_solver_module, 42, 5.0, 100),
    ?assertEqual(error, R#game_result.state),
    %% undef = function/module not found.
    case R#game_result.error of
        {error, undef} -> ok;
        Other -> ?assertMatch({error, undef}, Other)
    end.

zero_wallclock_returns_wall_clock_expired_test() ->
    R = runner_canonical:play_game(test_solver_w, 42, 0.0, 100),
    ?assertEqual(wall_clock_expired, R#game_result.state),
    ?assertEqual(0, R#game_result.moves).

max_moves_cap_terminates_loop_test() ->
    R = runner_canonical:play_game(test_solver_w, 42, 30.0, 5),
    %% Either we hit the cap, or 5 always-w moves happened to lose.
    ?assert(R#game_result.state =:= max_moves_reached
            orelse R#game_result.state =:= lost),
    ?assert(R#game_result.moves =< 5).
