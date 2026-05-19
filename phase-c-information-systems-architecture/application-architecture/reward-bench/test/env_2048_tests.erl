%% @doc EUnit suite for env_2048.
-module(env_2048_tests).
-include_lib("eunit/include/eunit.hrl").

%% --- compress_and_merge_row_left ---

empty_row_unchanged_test() ->
    ?assertEqual({[0,0,0,0], 0, false},
                 env_2048:compress_and_merge_row_left([0,0,0,0])).

slide_only_no_merge_test() ->
    ?assertEqual({[2,4,0,0], 0, true},
                 env_2048:compress_and_merge_row_left([0,2,0,4])).

single_pair_merges_to_double_test() ->
    ?assertEqual({[4,0,0,0], 4, true},
                 env_2048:compress_and_merge_row_left([2,2,0,0])).

triplet_merges_first_pair_only_test() ->
    ?assertEqual({[4,2,0,0], 4, true},
                 env_2048:compress_and_merge_row_left([2,2,2,0])).

quadruplet_merges_two_pairs_test() ->
    ?assertEqual({[4,4,0,0], 8, true},
                 env_2048:compress_and_merge_row_left([2,2,2,2])).

mixed_values_no_merge_but_slides_test() ->
    %% [0,2,4,8] is not left-aligned -> slides to [2,4,8,0], no merges.
    ?assertEqual({[2,4,8,0], 0, true},
                 env_2048:compress_and_merge_row_left([0,2,4,8])).

already_left_aligned_unchanged_test() ->
    ?assertEqual({[2,4,0,0], 0, false},
                 env_2048:compress_and_merge_row_left([2,4,0,0])).

larger_values_merge_test() ->
    ?assertEqual({[16,0,0,0], 16, true},
                 env_2048:compress_and_merge_row_left([8,8,0,0])).

%% --- new_board ---

new_board_has_two_nonzero_tiles_test() ->
    GS = env_2048:new_board(42),
    Flat = lists:flatten(env_2048:board(GS)),
    NonZero = [X || X <- Flat, X =/= 0],
    ?assertEqual(2, length(NonZero)),
    ?assert(lists:all(fun(X) -> X =:= 2 orelse X =:= 4 end, NonZero)).

new_board_deterministic_for_same_seed_test() ->
    GS1 = env_2048:new_board(42),
    GS2 = env_2048:new_board(42),
    ?assertEqual(env_2048:board(GS1), env_2048:board(GS2)).

new_board_varies_with_seed_test() ->
    Boards = [env_2048:board(env_2048:new_board(S)) || S <- [1, 2, 3, 4, 5]],
    Unique = lists:usort(Boards),
    %% Not all 5 must differ, but at least 2 should.
    ?assert(length(Unique) >= 2).

new_board_starts_at_zero_score_and_moves_test() ->
    GS = env_2048:new_board(42),
    ?assertEqual(0, env_2048:score(GS)),
    ?assertEqual(0, env_2048:moves(GS)).

%% --- step ---

step_some_action_changes_fresh_board_test() ->
    %% On a fresh 2-tile board, at least one direction must yield a change.
    GS = env_2048:new_board(42),
    ChangedAny = lists:any(fun(A) ->
        {_, C} = env_2048:step(GS, A),
        C
    end, [w, a, s, d]),
    ?assert(ChangedAny).

step_changing_action_increments_moves_test() ->
    GS = env_2048:new_board(42),
    %% Find an action that changes the board.
    [Action | _] = [A || A <- [w, a, s, d],
                         element(2, env_2048:step(GS, A))],
    {GS1, true} = env_2048:step(GS, Action),
    ?assertEqual(env_2048:moves(GS) + 1, env_2048:moves(GS1)).

step_non_changing_action_keeps_state_test() ->
    %% Find an action that does NOT change the board (if any exists for
    %% this seed). If all four actions change, skip — that's also valid.
    GS = env_2048:new_board(42),
    case [A || A <- [w, a, s, d],
               not element(2, env_2048:step(GS, A))] of
        [Action | _] ->
            {GS1, false} = env_2048:step(GS, Action),
            ?assertEqual(env_2048:moves(GS), env_2048:moves(GS1)),
            ?assertEqual(env_2048:board(GS), env_2048:board(GS1));
        [] ->
            ok  %% all directions change; nothing to assert
    end.

%% --- max_tile / is_lost ---

max_tile_on_fresh_board_is_2_or_4_test() ->
    GS = env_2048:new_board(42),
    M = env_2048:max_tile(GS),
    ?assert(M =:= 2 orelse M =:= 4).

is_lost_false_on_fresh_board_test() ->
    GS = env_2048:new_board(42),
    ?assertNot(env_2048:is_lost(GS)).
