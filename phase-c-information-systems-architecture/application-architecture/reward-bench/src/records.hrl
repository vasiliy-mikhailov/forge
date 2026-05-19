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

-record(submission, {
    body         :: binary(),
    score        :: float(),
    walltime_sec :: float()
}).

-record(context_snapshot, {
    env_spec            :: binary(),
    best_so_far         = undefined :: #submission{} | undefined,
    history_digest      = []        :: [#submission{}],
    iters_remaining     = 1         :: non_neg_integer(),
    %% Per-game Solver-execution wallclock cap (HARD_WALL_SEC,
    %% see SPEC.md). Flows through to canonical_scorer's dev test
    %% from solution_generator and to canonical_scorer's canonical
    %% scoring from orchestrator.
    budget_sec_per_seed = 5.0       :: float()
}).

-record(env, {
    canonical_scorer :: module(),
    model_client     :: pid(),
    env_spec         :: binary()
}).

-record(bench_config, {
    max_iters     = 1    :: pos_integer(),
    hard_wall_sec = 60.0 :: float()
}).
