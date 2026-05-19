%% @doc §5 fitness function — no `file:` calls above the Runner.
%%
%% Only bench_main.erl legitimately reads SKILL_tier1.md at startup;
%% no other src/*.erl may call into the `file:` module. Static check
%% via source-text scan (good enough — the bench is small).
-module(fitness_no_file_io_above_runner_tests).
-include_lib("eunit/include/eunit.hrl").

-define(ALLOWED_FILES_WITH_FILE_CALLS, [
    "bench_main.erl"  %% reads SKILL_tier1.md at CLI start
]).

no_file_module_calls_outside_allowlist_test() ->
    Files = fitness_helpers:src_files(),
    Violators = lists:filtermap(
        fun(Path) ->
            Name = filename:basename(Path),
            case lists:member(Name, ?ALLOWED_FILES_WITH_FILE_CALLS) of
                true -> false;
                false ->
                    Src = fitness_helpers:read_src(Path),
                    case re:run(Src, <<"\\bfile:">>, [{capture, none}]) of
                        match -> {true, Name};
                        nomatch -> false
                    end
            end
        end, Files),
    ?assertEqual([], Violators).
