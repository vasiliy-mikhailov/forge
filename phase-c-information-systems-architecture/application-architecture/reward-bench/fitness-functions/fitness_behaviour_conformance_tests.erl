%% @doc Fitness function — every behaviour-declaring module has at
%% least one production impl that declares it.
-module(fitness_behaviour_conformance_tests).
-include_lib("eunit/include/eunit.hrl").

beam_canonical_scorer_implements_canonical_scorer_test() ->
    Attrs = beam_canonical_scorer:module_info(attributes),
    Bs = proplists:get_value(behaviour, Attrs, [])
         ++ proplists:get_value(behavior,  Attrs, []),
    ?assert(lists:member(canonical_scorer, Bs),
            "beam_canonical_scorer must declare -behaviour(canonical_scorer)").
