%% @doc Fitness function — no Python-era stragglers in src/. Catches
%% docstring drift and copy-paste from the old bench.
-module(fitness_no_python_stragglers_tests).
-include_lib("eunit/include/eunit.hrl").

-define(PROHIBITED_PATTERNS, [
    <<"submission\\.py">>,
    <<"class Solver">>,
    <<"transitions library">>,
    <<"\\.pydantic\\b">>,
    <<"OpenHands">>,
    <<"condenser">>,
    <<"ralph">>,
    <<"agent_loop">>
]).

src_has_no_python_era_strings_test() ->
    Files = fitness_helpers:src_files(),
    Violators = lists:flatten(
        [check_file(F) || F <- Files]),
    ?assertEqual([], Violators).

check_file(Path) ->
    Src = fitness_helpers:read_src(Path),
    Name = filename:basename(Path),
    [{Name, Pat}
       || Pat <- ?PROHIBITED_PATTERNS,
          re:run(Src, Pat, [{capture, none}, caseless]) =:= match].
