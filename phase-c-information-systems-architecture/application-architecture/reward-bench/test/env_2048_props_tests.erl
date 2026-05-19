%% @doc EUnit wrappers around the env_2048_props PropEr properties.
%% Split from env_2048_props.erl because eunit.hrl and proper.hrl
%% both define LET / FORALL macros and cannot be -included into
%% the same module.
-module(env_2048_props_tests).
-include_lib("eunit/include/eunit.hrl").

-define(NUMTESTS, 100).
-define(OPTS, [{numtests, ?NUMTESTS}, quiet]).

compress_preserves_tile_sum_test_() ->
    {timeout, 30,
     ?_assert(proper:quickcheck(
                 env_2048_props:prop_compress_preserves_tile_sum(), ?OPTS))}.

new_board_deterministic_test_() ->
    {timeout, 30,
     ?_assert(proper:quickcheck(
                 env_2048_props:prop_new_board_deterministic_for_same_seed(),
                 ?OPTS))}.

step_no_change_preserves_state_test_() ->
    {timeout, 60,
     ?_assert(proper:quickcheck(
                 env_2048_props:prop_step_no_change_preserves_state(),
                 ?OPTS))}.

step_change_advances_moves_and_does_not_decrease_score_test_() ->
    {timeout, 60,
     ?_assert(proper:quickcheck(
                 env_2048_props:prop_step_change_advances_moves_and_does_not_decrease_score(),
                 ?OPTS))}.
