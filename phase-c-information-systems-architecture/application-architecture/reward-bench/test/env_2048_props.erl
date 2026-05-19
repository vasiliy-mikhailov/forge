%% @doc PropEr properties for env_2048 invariants. Pure PropEr —
%% no EUnit macros here to avoid the LET / FORALL clash. EUnit
%% wrappers live in env_2048_props_tests.erl.
-module(env_2048_props).
-include_lib("proper/include/proper.hrl").

-export([prop_compress_preserves_tile_sum/0,
         prop_new_board_deterministic_for_same_seed/0,
         prop_step_no_change_preserves_state/0,
         prop_step_change_advances_moves_and_does_not_decrease_score/0]).

%% =====================================================================
%% Generators

tile() ->
    elements([0, 0, 0, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]).

row() ->
    vector(4, tile()).

action() ->
    elements([w, a, s, d]).

seed() ->
    non_neg_integer().

%% =====================================================================
%% Properties

%% Compress preserves the sum of tile values — merging
%% N+N = 2N does not change the total, only the number of tiles
%% and their values. (Compress is NOT idempotent in general:
%% compress([2,2,2,2]) -> [4,4,0,0], whose compress is [8,0,0,0].)
prop_compress_preserves_tile_sum() ->
    ?FORALL(Row, row(),
        begin
            {Row1, _Gain, _Changed} =
                env_2048:compress_and_merge_row_left(Row),
            lists:sum(Row) =:= lists:sum(Row1)
        end).

%% Same seed -> same starting board.
prop_new_board_deterministic_for_same_seed() ->
    ?FORALL(Seed, seed(),
        env_2048:board(env_2048:new_board(Seed))
            =:= env_2048:board(env_2048:new_board(Seed))).

%% step/2 returning {_, false} (action had no effect) leaves
%% board, score, and moves unchanged.
prop_step_no_change_preserves_state() ->
    ?FORALL({Seed, Action}, {seed(), action()},
        begin
            GS = env_2048:new_board(Seed),
            case env_2048:step(GS, Action) of
                {GS1, false} ->
                    env_2048:board(GS)  =:= env_2048:board(GS1)
                    andalso env_2048:score(GS) =:= env_2048:score(GS1)
                    andalso env_2048:moves(GS) =:= env_2048:moves(GS1);
                {_, true} ->
                    true
            end
        end).

%% step/2 returning {_, true} increments moves by exactly 1 and
%% never decreases the score.
prop_step_change_advances_moves_and_does_not_decrease_score() ->
    ?FORALL({Seed, Action}, {seed(), action()},
        begin
            GS = env_2048:new_board(Seed),
            case env_2048:step(GS, Action) of
                {GS1, true} ->
                    env_2048:moves(GS1) =:= env_2048:moves(GS) + 1
                    andalso env_2048:score(GS1) >= env_2048:score(GS);
                {_, false} ->
                    true
            end
        end).
