%% @doc EUnit suite for beam_canonical_scorer.
-module(beam_canonical_scorer_tests).
-include_lib("eunit/include/eunit.hrl").
-include("records.hrl").

-define(TRIVIAL_W_SOURCE, <<
    "-module(submission).\n"
    "-export([move/1]).\n"
    "move(_) -> w.\n"
>>).

trivial_solver_compiles_and_scores_test() ->
    R = beam_canonical_scorer:score_body(?TRIVIAL_W_SOURCE, [42, 43], 5.0),
    ?assertEqual(2, R#attempt_result.n_games),
    ?assertEqual(undefined, R#attempt_result.compile_error),
    ?assert(R#attempt_result.mean_score >= 0.0),
    ?assert(R#attempt_result.aggregate_walltime_sec >= 0.0),
    ?assertEqual(2, length(R#attempt_result.games)).

trivial_solver_games_all_terminate_test() ->
    R = beam_canonical_scorer:score_body(?TRIVIAL_W_SOURCE, [42, 43, 44], 5.0),
    States = [G#game_result.state || G <- R#attempt_result.games],
    %% Always-w eventually loses or hits the move cap; never just runs.
    ?assert(lists:all(fun(S) ->
        lists:member(S, [lost, max_moves_reached, won])
    end, States)).

compile_error_returns_zero_score_with_compile_error_set_test() ->
    Bad = <<"this is not valid erlang at all !!!">>,
    R = beam_canonical_scorer:score_body(Bad, [42], 5.0),
    ?assertEqual(0.0, R#attempt_result.mean_score),
    ?assertEqual([], R#attempt_result.games),
    ?assertNotEqual(undefined, R#attempt_result.compile_error).

empty_body_returns_zero_score_test() ->
    R = beam_canonical_scorer:score_body(<<>>, [42], 5.0),
    ?assertEqual(0.0, R#attempt_result.mean_score),
    ?assertNotEqual(undefined, R#attempt_result.compile_error).

module_purged_after_scoring_test() ->
    _ = beam_canonical_scorer:score_body(?TRIVIAL_W_SOURCE, [42], 5.0),
    ?assertEqual(false, code:is_loaded(submission)).

via_canonical_scorer_dispatch_test() ->
    %% canonical_scorer:score_body/4 dispatches to the impl module.
    R = canonical_scorer:score_body(beam_canonical_scorer,
                                    ?TRIVIAL_W_SOURCE, [42], 5.0),
    ?assertEqual(1, R#attempt_result.n_games),
    ?assertEqual(undefined, R#attempt_result.compile_error).

aggregate_mean_computed_correctly_test() ->
    %% A solver that always loses on first invalid attempt → score 0.
    %% Mean across N seeds = 0. Use trivial solver and check N=1 mean=score.
    R = beam_canonical_scorer:score_body(?TRIVIAL_W_SOURCE, [42], 5.0),
    [G] = R#attempt_result.games,
    ?assertEqual(float(G#game_result.score), R#attempt_result.mean_score).

memory_bombing_solver_gets_killed_test() ->
    %% Per SOLUTION-ARCHITECTURE.md §5: a Solver that tries to
    %% allocate a huge data structure hits the per-game process'''s
    %% max_heap_size cap and is killed cleanly. Game state goes to
    %% error; the bench continues with the next seed.
    Body = <<
        "-module(submission).
"
        "-export([move/1]).
"
        "move(_) ->
"
        "    _ = lists:duplicate(100000000, deadbeef),
"
        "    w.
"
    >>,
    R = beam_canonical_scorer:score_body(Body, [42], 5.0),
    [G] = R#attempt_result.games,
    ?assertEqual(error, G#game_result.state),
    ?assertMatch({process_died, _}, G#game_result.error).
