%% @doc Fitness function — concurrency is corralled. Only the
%% canonical scorer spawns processes (one per seed for game plays).
%% Anywhere else means an architectural slip into uncontrolled
%% concurrency.
-module(fitness_no_unrestricted_spawn_tests).
-include_lib("eunit/include/eunit.hrl").

-define(ALLOWED_SPAWNERS, [
    "beam_canonical_scorer.erl"
    %% reward_bench_sup spawns indirectly via supervisor:start_link,
    %% which doesn't use the spawn family of BIFs and so doesn't
    %% match the regex below.
]).

-define(SPAWN_RE,
    %% Matches spawn / spawn_link / spawn_monitor / spawn_opt /
    %% erlang:spawn{,_link,_monitor,_opt}. Stops at the open paren so
    %% comments / strings / unrelated identifiers don't match.
    <<"\\b(?:erlang:)?spawn(?:_link|_monitor|_opt)?\\s*\\(">>).

no_spawn_outside_canonical_scorer_test() ->
    Files = fitness_helpers:src_files(),
    Violators = lists:filtermap(
        fun(Path) ->
            Name = filename:basename(Path),
            case lists:member(Name, ?ALLOWED_SPAWNERS) of
                true -> false;
                false ->
                    Src = fitness_helpers:read_src(Path),
                    case re:run(Src, ?SPAWN_RE, [{capture, none}]) of
                        match -> {true, Name};
                        nomatch -> false
                    end
            end
        end, Files),
    ?assertEqual([], Violators).
