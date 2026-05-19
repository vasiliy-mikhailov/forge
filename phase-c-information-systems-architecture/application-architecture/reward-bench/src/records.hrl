%% Shared records — included by env_2048 and downstream modules.

-record(game_state, {
    board     :: [[non_neg_integer()]],
    score = 0 :: non_neg_integer(),
    rand      :: rand:state(),
    moves = 0 :: non_neg_integer()
}).

-record(game_result, {
    score        :: non_neg_integer(),
    max_tile     :: non_neg_integer(),
    moves        :: non_neg_integer(),
    state        :: won | lost | wall_clock_expired
                  | error | max_moves_reached,
    walltime_sec :: float(),
    error        :: undefined | term()
}).

-record(attempt_result, {
    mean_score             :: float(),
    median_score           :: float(),
    n_games                :: non_neg_integer(),
    aggregate_walltime_sec :: float(),
    games = []             :: [#game_result{}],
    compile_error          :: undefined | term()
}).
