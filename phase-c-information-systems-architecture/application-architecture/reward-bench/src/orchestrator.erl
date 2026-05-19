%% @doc §2 Orchestrator. Drives N iters: per-iter snapshot from
%% cumulative state, call solution_generator:generate/3, score
%% the body via canonical_scorer on canonical seeds, yield a
%% #submission{}.
%%
%% Stateless module — cumulative state is the iter loop's
%% accumulator, not a process.
-module(orchestrator).
-export([orchestrate/2]).

-include("records.hrl").

%% Canonical held-out seeds. Held out from dev seeds (2000-2004
%% in solution_generator). Twenty games is the bench measurement
%% surface.
-define(CANONICAL_SEEDS, lists:seq(1000, 1019)).
-define(GAME_HARD_WALL_SEC, 5.0).

-spec orchestrate(#env{}, #bench_config{}) -> [#submission{}].
orchestrate(Env, Cfg) ->
    MaxIters = Cfg#bench_config.max_iters,
    HardWallSec = Cfg#bench_config.hard_wall_sec,
    iterate(Env, MaxIters, MaxIters, HardWallSec, [], undefined).

%% =====================================================================
%% Private

iterate(_Env, _Total, 0, _HW, Subs, _Best) ->
    lists:reverse(Subs);
iterate(Env, Total, Remaining, HW, Subs, Best) ->
    Snap = build_snapshot(Env, Total, Remaining, HW, Subs, Best),
    Body = solution_generator:generate(
        Env#env.model_client,
        Env#env.canonical_scorer,
        Snap),
    Sub = score_to_submission(Env, Body),
    Best1 = pick_best(Sub, Best),
    iterate(Env, Total, Remaining - 1, HW, [Sub | Subs], Best1).

build_snapshot(Env, Total, Remaining, HW, Subs, Best) ->
    %% Per-iter wallclock budget: divide the bench-level HW evenly
    %% across iters. The SolutionGenerator's reasoning loop receives
    %% this as time_remaining_sec.
    PerIter = HW / Total,
    #context_snapshot{
        env_spec            = Env#env.env_spec,
        best_so_far         = Best,
        history_digest      = lists:reverse(Subs),
        iters_remaining     = Remaining,
        time_remaining_sec  = PerIter,
        budget_sec_per_seed = ?GAME_HARD_WALL_SEC
    }.

score_to_submission(Env, Body) ->
    AR = canonical_scorer:score_body(
        Env#env.canonical_scorer,
        Body,
        ?CANONICAL_SEEDS,
        ?GAME_HARD_WALL_SEC),
    #submission{
        body         = Body,
        score        = AR#attempt_result.mean_score,
        walltime_sec = AR#attempt_result.aggregate_walltime_sec
    }.

pick_best(Sub, undefined) ->
    Sub;
pick_best(Sub, Best) when Sub#submission.score > Best#submission.score ->
    Sub;
pick_best(_Sub, Best) ->
    Best.
