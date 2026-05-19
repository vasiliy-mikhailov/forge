%% @doc Fitness function — reward_bench_sup boots cleanly and exposes
%% the expected children shape. Cycle 233 ships zero children;
%% downstream cycles add llm_client / canonical_scorer as needed and
%% this test pins the count.
-module(fitness_supervision_tree_shape_tests).
-include_lib("eunit/include/eunit.hrl").

%% Expected child count at the top-level supervisor. Bump when
%% supervised children are added (e.g., a singleton llm_client).
-define(EXPECTED_TOP_LEVEL_CHILDREN, 0).

supervisor_starts_and_returns_expected_child_count_test() ->
    {ok, Pid} = reward_bench_sup:start_link(),
    try
        Children = supervisor:which_children(Pid),
        ?assertEqual(?EXPECTED_TOP_LEVEL_CHILDREN, length(Children))
    after
        unlink(Pid),
        exit(Pid, shutdown),
        wait_for_exit(Pid, 1000)
    end.

wait_for_exit(Pid, Timeout) ->
    Ref = erlang:monitor(process, Pid),
    receive
        {'DOWN', Ref, process, Pid, _} -> ok
    after Timeout ->
        ok
    end.
