%% @doc Top-level supervisor per SOLUTION-ARCHITECTURE.md §2.
%% Children land in later cycles: llm_client, canonical_scorer (singleton).
-module(reward_bench_sup).
-behaviour(supervisor).

-export([start_link/0]).
-export([init/1]).

-spec start_link() -> {ok, pid()}.
start_link() ->
    supervisor:start_link({local, ?MODULE}, ?MODULE, []).

-spec init([]) -> {ok, {supervisor:sup_flags(), [supervisor:child_spec()]}}.
init([]) ->
    SupFlags = #{strategy => one_for_one,
                 intensity => 1,
                 period => 5},
    ChildSpecs = [],
    {ok, {SupFlags, ChildSpecs}}.
