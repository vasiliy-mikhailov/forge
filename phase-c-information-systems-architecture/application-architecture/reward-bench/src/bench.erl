%% @doc §1 bench use case.
%%
%% bench :: env() -> bench_config() -> submission()
%% bench(Env, Cfg) = argmaxBy(.score)(orchestrator:orchestrate(Env, Cfg))
%%
%% Pure composition over the Orchestrator port.
-module(bench).
-export([bench/2]).

-include("records.hrl").

-spec bench(#env{}, #bench_config{}) -> #submission{}.
bench(Env, Cfg) ->
    case orchestrator:orchestrate(Env, Cfg) of
        [] ->
            #submission{body = <<>>, score = 0.0, walltime_sec = 0.0};
        [First | Rest] ->
            lists:foldl(fun pick_best/2, First, Rest)
    end.

pick_best(S, Acc) when S#submission.score > Acc#submission.score -> S;
pick_best(_S, Acc) -> Acc.
