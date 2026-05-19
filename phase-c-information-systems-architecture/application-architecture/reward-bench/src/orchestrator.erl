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

-spec orchestrate(#env{}, #bench_config{}) -> [#submission{}].
orchestrate(Env, Cfg) ->
    MaxIters = Cfg#bench_config.max_iters,
    iterate(Env, Cfg, MaxIters, [], undefined).

%% =====================================================================
%% Private

iterate(_Env, _Cfg, 0, Subs, _Best) ->
    lists:reverse(Subs);
iterate(Env, Cfg, Remaining, Subs, Best) ->
    Snap = build_snapshot(Env, Cfg, Remaining, Subs, Best),
    Body = solution_generator:generate(
        Env#env.model_client,
        Env#env.canonical_scorer,
        Snap),
    Sub = score_to_submission(Env, Cfg, Body),
    Best1 = pick_best(Sub, Best),
    iterate(Env, Cfg, Remaining - 1, [Sub | Subs], Best1).

build_snapshot(Env, Cfg, Remaining, Subs, Best) ->
    %% budget_sec_per_seed = the per-Solver-game wallclock cap
    %% (HARD_WALL_SEC). Used by canonical_scorer for both dev tests
    %% (via solution_generator) and canonical scoring (here).
    #context_snapshot{
        env_spec            = Env#env.env_spec,
        best_so_far         = Best,
        history_digest      = lists:reverse(Subs),
        iters_remaining     = Remaining,
        budget_sec_per_seed = Cfg#bench_config.hard_wall_sec
    }.

score_to_submission(Env, Cfg, Body) ->
    AR = canonical_scorer:score_body(
        Env#env.canonical_scorer,
        Body,
        ?CANONICAL_SEEDS,
        Cfg#bench_config.hard_wall_sec),
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
