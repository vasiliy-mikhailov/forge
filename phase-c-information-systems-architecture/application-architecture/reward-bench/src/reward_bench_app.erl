%% @doc reward_bench application — entry point per SOLUTION-ARCHITECTURE.md.
-module(reward_bench_app).
-behaviour(application).

-export([start/2, stop/1]).

-spec start(application:start_type(), term()) ->
    {ok, pid()} | {error, term()}.
start(_StartType, _StartArgs) ->
    reward_bench_sup:start_link().

-spec stop(term()) -> ok.
stop(_State) ->
    ok.
