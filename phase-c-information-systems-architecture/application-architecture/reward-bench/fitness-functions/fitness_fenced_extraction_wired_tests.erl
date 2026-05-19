%% @doc §4 fitness function — solution_generator must use
%% extract_fenced_erlang. If a refactor accidentally strips the call,
%% the SolutionGenerator would still compile but return garbage.
-module(fitness_fenced_extraction_wired_tests).
-include_lib("eunit/include/eunit.hrl").

solution_generator_calls_extract_fenced_erlang_test() ->
    Src = fitness_helpers:read_src("src/solution_generator.erl"),
    ?assertNotEqual(nomatch,
                    binary:match(Src, <<"extract_fenced_erlang">>)).
