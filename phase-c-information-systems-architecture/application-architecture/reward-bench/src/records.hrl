%% Shared records — included by env_2048 and downstream modules.

-record(game_state, {
    board     :: [[non_neg_integer()]],
    score = 0 :: non_neg_integer(),
    rand      :: rand:state(),
    moves = 0 :: non_neg_integer()
}).
