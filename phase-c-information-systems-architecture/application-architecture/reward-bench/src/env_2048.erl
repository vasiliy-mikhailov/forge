%% @doc 2048 game environment per SOLUTION-ARCHITECTURE.md §5.
%%
%% State is the #game_state{} record (see records.hrl). All
%% functions are pure — they take a state and return a new state.
%% Random tile spawning is deterministic via the seeded rand
%% state carried inside #game_state{}.
%%
%% Action atoms: w (up), a (left), s (down), d (right).
-module(env_2048).

-export([new_board/1, step/2,
         board/1, score/1, max_tile/1, moves/1,
         is_lost/1]).
%% Exported for unit tests; not part of the public game API.
-export([compress_and_merge_row_left/1]).

-include("records.hrl").

-define(BOARD_SIZE, 4).
-define(EMPTY_BOARD, [[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]]).

-spec new_board(non_neg_integer()) -> #game_state{}.
new_board(Seed) ->
    Rand0 = rand:seed_s(exsss, {Seed, Seed, Seed}),
    GS0 = #game_state{board = ?EMPTY_BOARD, rand = Rand0},
    spawn_tile(spawn_tile(GS0)).

-spec board(#game_state{}) -> [[non_neg_integer()]].
board(#game_state{board = B}) -> B.

-spec score(#game_state{}) -> non_neg_integer().
score(#game_state{score = S}) -> S.

-spec max_tile(#game_state{}) -> non_neg_integer().
max_tile(#game_state{board = B}) -> lists:max(lists:flatten(B)).

-spec moves(#game_state{}) -> non_neg_integer().
moves(#game_state{moves = M}) -> M.

-spec step(#game_state{}, w | a | s | d) -> {#game_state{}, boolean()}.
step(GS = #game_state{board = B, score = S, moves = M}, Action) ->
    {NewB, Gain, Changed} = apply_action(B, Action),
    case Changed of
        false ->
            {GS, false};
        true ->
            GS1 = GS#game_state{board = NewB,
                                score = S + Gain,
                                moves = M + 1},
            {spawn_tile(GS1), true}
    end.

-spec is_lost(#game_state{}) -> boolean().
is_lost(#game_state{board = B}) ->
    lists:all(fun(A) ->
        {_, _, Changed} = apply_action(B, A),
        not Changed
    end, [w, a, s, d]).

%% =====================================================================
%% Private — action mechanics

apply_action(B, a) -> move_left(B);
apply_action(B, d) -> move_right(B);
apply_action(B, w) -> move_up(B);
apply_action(B, s) -> move_down(B).

move_left(Board) ->
    Tagged = [compress_and_merge_row_left(R) || R <- Board],
    {[R || {R, _, _} <- Tagged],
     lists:sum([G || {_, G, _} <- Tagged]),
     lists:any(fun({_, _, C}) -> C end, Tagged)}.

move_right(Board) ->
    {NewB, G, C} = move_left([lists:reverse(R) || R <- Board]),
    {[lists:reverse(R) || R <- NewB], G, C}.

move_up(Board) ->
    {NewB, G, C} = move_left(transpose(Board)),
    {transpose(NewB), G, C}.

move_down(Board) ->
    {NewB, G, C} = move_right(transpose(Board)),
    {transpose(NewB), G, C}.

transpose([[]|_]) -> [];
transpose(M) ->
    [[H || [H|_] <- M] | transpose([T || [_|T] <- M])].

-spec compress_and_merge_row_left([non_neg_integer()]) ->
    {[non_neg_integer()], non_neg_integer(), boolean()}.
compress_and_merge_row_left(Row) ->
    Tiles = [X || X <- Row, X =/= 0],
    {Merged, Gain} = merge_tiles(Tiles, 0),
    N = length(Row),
    Padded = Merged ++ lists:duplicate(N - length(Merged), 0),
    {Padded, Gain, Padded =/= Row}.

merge_tiles([], Acc) -> {[], Acc};
merge_tiles([X], Acc) -> {[X], Acc};
merge_tiles([X, X | Rest], Acc) ->
    V = X * 2,
    {Tail, Acc1} = merge_tiles(Rest, Acc + V),
    {[V | Tail], Acc1};
merge_tiles([X, Y | Rest], Acc) ->
    {Tail, Acc1} = merge_tiles([Y | Rest], Acc),
    {[X | Tail], Acc1}.

%% =====================================================================
%% Private — random tile spawning

spawn_tile(GS = #game_state{board = B, rand = R}) ->
    case empty_cells(B) of
        [] ->
            GS;
        Empties ->
            {Idx, R1} = rand:uniform_s(length(Empties), R),
            {RIdx, CIdx} = lists:nth(Idx, Empties),
            {V, R2} = case rand:uniform_s(10, R1) of
                          {1, RR} -> {4, RR};
                          {_, RR} -> {2, RR}
                      end,
            GS#game_state{board = set_cell(B, RIdx, CIdx, V),
                          rand = R2}
    end.

empty_cells(Board) ->
    [{RIdx, CIdx} || {RIdx, Row} <- enumerate(Board, 1),
                     {CIdx, V}   <- enumerate(Row, 1),
                     V =:= 0].

enumerate(L, N) -> enumerate(L, N, []).
enumerate([], _, Acc) -> lists:reverse(Acc);
enumerate([H | T], N, Acc) -> enumerate(T, N + 1, [{N, H} | Acc]).

set_cell(Board, RowIdx, ColIdx, V) ->
    {PreRows, [Row | PostRows]} = lists:split(RowIdx - 1, Board),
    {PreCols, [_Old | PostCols]} = lists:split(ColIdx - 1, Row),
    NewRow = PreCols ++ [V | PostCols],
    PreRows ++ [NewRow | PostRows].
