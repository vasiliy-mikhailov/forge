%% @doc In-VM canonical scorer per SOLUTION-ARCHITECTURE.md §5.
%%
%% Takes Erlang module source as a binary, compiles via
%% compile:forms/2, loads via code:load_binary/3, spawns one
%% monitored process per seed running runner_canonical:play_game,
%% aggregates #game_result{}s to a single #attempt_result{}.
%%
%% Module is code:purge + code:delete-d after scoring so the next
%% attempt starts clean.
-module(beam_canonical_scorer).
-behaviour(canonical_scorer).

-export([score_body/3]).

-include("records.hrl").

-define(GAME_MOVE_CAP, 10000).
-define(COLLECT_GRACE_MS, 5000).

%% Per-game process heap cap. 10_000_000 words ≈ 80 MB on 64-bit.
%% The 2048 game state is sub-1 MB; this cap kills runaway Solvers
%% (infinite recursion building lists, etc.) before they OOM the
%% whole BEAM. See SOLUTION-ARCHITECTURE.md §5.
-define(MAX_HEAP_WORDS, 10_000_000).

-spec score_body(binary(), [non_neg_integer()], number()) ->
    #attempt_result{}.
score_body(BodyBin, Seeds, HardWallSec) ->
    case compile_body(BodyBin) of
        {ok, ModuleName, BeamBin} ->
            {module, ModuleName} =
                code:load_binary(ModuleName, "nofile", BeamBin),
            try
                Results = run_games(ModuleName, Seeds, HardWallSec),
                aggregate(Results)
            after
                code:purge(ModuleName),
                code:delete(ModuleName)
            end;
        {error, Reason} ->
            #attempt_result{
                mean_score = 0.0,
                median_score = 0.0,
                n_games = length(Seeds),
                aggregate_walltime_sec = 0.0,
                games = [],
                compile_error = Reason
            }
    end.

%% =====================================================================
%% Compile

compile_body(BodyBin) when is_binary(BodyBin) ->
    case erl_scan:string(unicode:characters_to_list(BodyBin)) of
        {ok, Tokens, _End} ->
            case parse_forms(Tokens, [], []) of
                {ok, Forms} ->
                    case compile:forms(Forms, [binary, return_errors,
                                               return_warnings]) of
                        {ok, ModuleName, BeamBin} ->
                            {ok, ModuleName, BeamBin};
                        {ok, ModuleName, BeamBin, _Warnings} ->
                            {ok, ModuleName, BeamBin};
                        Error ->
                            {error, {compile, Error}}
                    end;
                {error, _} = Err ->
                    Err
            end;
        {error, ScanErr, _} ->
            {error, {scan, ScanErr}}
    end.

%% Walk a token stream, split at {dot, _}, parse each form.
parse_forms([], [], Acc) ->
    case Acc of
        [] -> {error, no_forms};
        _  -> {ok, lists:reverse(Acc)}
    end;
parse_forms([], Pending, _Acc) ->
    {error, {unterminated_form, lists:reverse(Pending)}};
parse_forms([{dot, _} = Dot | Rest], Pending, Acc) ->
    FormTokens = lists:reverse([Dot | Pending]),
    case erl_parse:parse_form(FormTokens) of
        {ok, Form}     -> parse_forms(Rest, [], [Form | Acc]);
        {error, _} = E -> E
    end;
parse_forms([T | Rest], Pending, Acc) ->
    parse_forms(Rest, [T | Pending], Acc).

%% =====================================================================
%% Run games (one Erlang process per seed)

run_games(ModuleName, Seeds, HardWallSec) ->
    Parent = self(),
    PidsRefs = lists:map(fun(Seed) ->
        spawn_monitor(fun() ->
            process_flag(max_heap_size, #{size => ?MAX_HEAP_WORDS,
                                          kill => true,
                                          error_logger => false}),
            R = runner_canonical:play_game(ModuleName, Seed, HardWallSec,
                                           ?GAME_MOVE_CAP),
            Parent ! {self(), R}
        end)
    end, Seeds),
    collect(PidsRefs, []).

collect([], Acc) ->
    lists:reverse(Acc);
collect([{Pid, Ref} | Rest], Acc) ->
    receive
        {Pid, R} ->
            %% Drain the DOWN message that follows normal exit.
            receive {'DOWN', Ref, process, _, _} -> ok
            after ?COLLECT_GRACE_MS -> ok
            end,
            collect(Rest, [R | Acc]);
        {'DOWN', Ref, process, _, Reason} ->
            R = #game_result{
                score = 0, max_tile = 0, moves = 0,
                state = error, walltime_sec = 0.0,
                error = {process_died, Reason}
            },
            collect(Rest, [R | Acc])
    end.

%% =====================================================================
%% Aggregate

aggregate([]) ->
    #attempt_result{
        mean_score = 0.0, median_score = 0.0,
        n_games = 0, aggregate_walltime_sec = 0.0, games = []
    };
aggregate(Results) ->
    Scores = [R#game_result.score || R <- Results],
    Walltime = lists:sum([R#game_result.walltime_sec || R <- Results]),
    N = length(Results),
    Mean = lists:sum(Scores) / N,
    Median = median(Scores),
    #attempt_result{
        mean_score             = float(Mean),
        median_score           = float(Median),
        n_games                = N,
        aggregate_walltime_sec = Walltime,
        games                  = Results
    }.

median(Scores) ->
    Sorted = lists:sort(Scores),
    N = length(Sorted),
    Mid = N div 2,
    case N rem 2 of
        1 -> float(lists:nth(Mid + 1, Sorted));
        0 -> (lists:nth(Mid, Sorted) + lists:nth(Mid + 1, Sorted)) / 2.0
    end.
