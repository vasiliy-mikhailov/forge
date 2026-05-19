%% @doc §4 SolutionGenerator reasoning loop. Pure Erlang, no SDK.
%%
%%   prompt -> LLM -> extract fenced erlang -> dev_test (canonical_scorer)
%%          -> append observation -> loop
%%
%% Bounded by:
%%   max_iters         hard cap on conversation turns
%%   min_iter_time_sec stops if remaining wallclock < this
%%   time_remaining_sec from #context_snapshot{} (the deadline)
%%
%% Returns the highest-scoring body seen across all iters (may be
%% empty if no iter ever produced a fenced block).
-module(solution_generator).

-export([generate/3, generate/4]).

-include("records.hrl").

-define(DEFAULT_MAX_ITERS, 8).
-define(DEFAULT_MIN_ITER_TIME_SEC, 5.0).
-define(DEFAULT_DEV_SEEDS, [2000, 2001, 2002, 2003, 2004]).
-define(DEFAULT_DEV_HARD_WALL_SEC, 3.0).

-spec generate(pid(), module(), #context_snapshot{}) -> binary().
generate(LLM, Scorer, Snapshot) ->
    generate(LLM, Scorer, Snapshot, #{}).

-spec generate(pid(), module(), #context_snapshot{}, map()) -> binary().
generate(LLM, Scorer, Snapshot, Opts) ->
    MaxIters    = maps:get(max_iters,         Opts, ?DEFAULT_MAX_ITERS),
    MinIterTime = maps:get(min_iter_time_sec, Opts, ?DEFAULT_MIN_ITER_TIME_SEC),
    DevSeeds    = maps:get(dev_seeds,         Opts, ?DEFAULT_DEV_SEEDS),
    DevHardWall = maps:get(dev_hard_wall_sec, Opts, ?DEFAULT_DEV_HARD_WALL_SEC),
    Spec = Snapshot#context_snapshot.env_spec,
    Msgs = [#{role => <<"user">>, content => Spec}],
    Deadline = erlang:monotonic_time(millisecond)
             + trunc(Snapshot#context_snapshot.time_remaining_sec * 1000),
    Best0 = #submission{body = <<>>, score = -1.0, walltime_sec = 0.0},
    Cfg = #{llm         => LLM,
            scorer      => Scorer,
            max_iters   => MaxIters,
            min_iter_ms => trunc(MinIterTime * 1000),
            dev_seeds   => DevSeeds,
            dev_hwsec   => DevHardWall},
    loop(Cfg, Msgs, Best0, Deadline, 0).

%% =====================================================================
%% Private

loop(#{max_iters := Max}, _Msgs, Best, _Deadline, Iter) when Iter >= Max ->
    Best#submission.body;
loop(Cfg, Msgs, Best, Deadline, Iter) ->
    Now = erlang:monotonic_time(millisecond),
    case Deadline - Now < maps:get(min_iter_ms, Cfg) of
        true  -> Best#submission.body;
        false -> iter(Cfg, Msgs, Best, Deadline, Iter)
    end.

iter(Cfg, Msgs, Best, Deadline, Iter) ->
    case llm_client:chat(maps:get(llm, Cfg), Msgs) of
        {error, _Reason} ->
            Best#submission.body;
        {ok, RespText} ->
            handle_response(Cfg, Msgs, Best, Deadline, Iter, RespText)
    end.

handle_response(Cfg, Msgs, Best, Deadline, Iter, RespText) ->
    case extract_fenced_erlang:extract(RespText,
                                       <<"-module(submission)">>) of
        <<>> ->
            NudgeMsg = append_turn(Msgs, RespText,
                <<"No fenced erlang block in your response. "
                  "Emit your Solver as a ```erlang ... ``` block.">>),
            loop(Cfg, NudgeMsg, Best, Deadline, Iter + 1);
        Body ->
            score_and_observe(Cfg, Msgs, Best, Deadline, Iter, RespText, Body)
    end.

score_and_observe(Cfg, Msgs, Best, Deadline, Iter, RespText, Body) ->
    AR = canonical_scorer:score_body(
            maps:get(scorer, Cfg),
            Body,
            maps:get(dev_seeds, Cfg),
            maps:get(dev_hwsec, Cfg)),
    Best1 = update_best(Best, Body, AR),
    Obs = format_observation(AR),
    NewMsgs = append_turn(Msgs, RespText, Obs),
    loop(Cfg, NewMsgs, Best1, Deadline, Iter + 1).

update_best(Best, Body, #attempt_result{compile_error = CE} = AR)
  when CE =:= undefined ->
    Score = AR#attempt_result.mean_score,
    case Score > Best#submission.score of
        true ->
            #submission{
                body         = Body,
                score        = Score,
                walltime_sec = AR#attempt_result.aggregate_walltime_sec
            };
        false ->
            Best
    end;
update_best(Best, _Body, _AR) ->
    Best.

append_turn(Msgs, Assistant, User) ->
    Msgs ++ [
        #{role => <<"assistant">>, content => Assistant},
        #{role => <<"user">>,      content => User}
    ].

format_observation(#attempt_result{compile_error = CE}) when CE =/= undefined ->
    list_to_binary(io_lib:format(
        "Your submission failed to compile:~n~p~n~n"
        "Fix the syntax / -module / -export / move/1 contract "
        "and emit a new fenced erlang block.",
        [CE]));
format_observation(#attempt_result{n_games = 0}) ->
    <<"No games ran. Check your move/1 implementation.">>;
format_observation(AR = #attempt_result{}) ->
    Games = AR#attempt_result.games,
    Lines = [list_to_binary(io_lib:format(
                "  game ~w: score=~w max_tile=~w moves=~w state=~p~n",
                [I, G#game_result.score,
                 G#game_result.max_tile,
                 G#game_result.moves,
                 G#game_result.state]))
              || {I, G} <- lists:zip(
                              lists:seq(1, length(Games)),
                              Games)],
    Header = io_lib:format(
        "Dev test (~w games): mean=~.2f median=~.2f total_wall=~.2fs~n",
        [AR#attempt_result.n_games,
         AR#attempt_result.mean_score,
         AR#attempt_result.median_score,
         AR#attempt_result.aggregate_walltime_sec]),
    iolist_to_binary([Header, Lines,
        "\nIterate to improve, or finalise by emitting your best "
        "version as the LAST fenced erlang block."]).
