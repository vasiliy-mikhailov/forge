%% @doc EUnit suite for compose_env_spec.
-module(compose_env_spec_tests).
-include_lib("eunit/include/eunit.hrl").

contains_task_section_test() ->
    Spec = compose_env_spec:compose(<<"my-skill-text">>, 60),
    ?assertNotEqual(nomatch, binary:match(Spec, <<"# Task">>)),
    ?assertNotEqual(nomatch, binary:match(Spec, <<"my-skill-text">>)).

contains_output_section_with_fenced_erlang_test() ->
    Spec = compose_env_spec:compose(<<"x">>, 60),
    ?assertNotEqual(nomatch, binary:match(Spec, <<"# Output">>)),
    ?assertNotEqual(nomatch, binary:match(Spec, <<"```erlang">>)).

contains_budget_with_seconds_test() ->
    Spec = compose_env_spec:compose(<<"x">>, 60),
    ?assertNotEqual(nomatch, binary:match(Spec, <<"# Budget">>)),
    ?assertNotEqual(nomatch, binary:match(Spec, <<"60 seconds">>)).

truncates_fractional_seconds_test() ->
    Spec = compose_env_spec:compose(<<"x">>, 60.7),
    ?assertNotEqual(nomatch, binary:match(Spec, <<"60 seconds">>)).

returns_binary_test() ->
    Spec = compose_env_spec:compose(<<"x">>, 60),
    ?assert(is_binary(Spec)).
