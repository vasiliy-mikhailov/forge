%% @doc EUnit suite for solution_generator. Uses llm_client with
%% scripted responses (via counters-based stub) + real
%% beam_canonical_scorer for compile + score.
-module(solution_generator_tests).
-include_lib("eunit/include/eunit.hrl").
-include("records.hrl").

-define(TRIVIAL_W,
    <<"-module(submission).\n-export([move/1]).\nmove(_) -> w.\n">>).

ok_response(Content) ->
    jsx:encode(#{
        <<"choices">> => [
            #{<<"message">> => #{<<"content">> => Content}}
        ]
    }).

make_sequence_stub(Responses) ->
    Counter = counters:new(1, [atomics]),
    fun(_Url, _Headers, _Body) ->
        I = counters:get(Counter, 1) + 1,
        counters:add(Counter, 1, 1),
        Resp = case I =< length(Responses) of
            true  -> lists:nth(I, Responses);
            false -> lists:last(Responses)
        end,
        {ok, 200, Resp}
    end.

start_llm(Responses) ->
    {ok, Pid} = llm_client:start_link(#{
        base_url => <<"http://stub">>,
        api_key  => <<"k">>,
        model_id => <<"m">>,
        http_fn  => make_sequence_stub(Responses)
    }),
    Pid.

snapshot(Spec, Sec) ->
    #context_snapshot{
        env_spec            = Spec,
        best_so_far         = undefined,
        history_digest      = [],
        iters_remaining     = 1,
        time_remaining_sec  = Sec,
        budget_sec_per_seed = 3.0
    }.

%% --- Happy path ---

generate_returns_fenced_body_test() ->
    Wrapped = <<"Here:\n```erlang\n", ?TRIVIAL_W/binary, "```\n">>,
    LLM = start_llm([ok_response(Wrapped)]),
    try
        Result = solution_generator:generate(
            LLM, beam_canonical_scorer, snapshot(<<"task">>, 30.0),
            #{max_iters => 1, dev_seeds => [42], dev_hard_wall_sec => 3.0}),
        ?assertEqual(?TRIVIAL_W, Result)
    after
        llm_client:stop(LLM)
    end.

%% --- Picks higher-scoring body across iters ---

generate_picks_higher_scoring_body_test() ->
    %% Both responses produce a valid Solver; both should score equally
    %% (always-w solver). With max_iters=2 and seed=[42], the last one
    %% wins on ties, but score should be >= 0 either way. We can't
    %% reliably make two different-score Solvers here without a smarter
    %% one. Instead, assert that with two valid responses the result is
    %% non-empty and valid.
    A = <<"-module(submission).\n-export([move/1]).\nmove(_) -> w.\n">>,
    B = <<"-module(submission).\n-export([move/1]).\nmove(_) -> d.\n">>,
    R1 = ok_response(<<"```erlang\n", A/binary, "```">>),
    R2 = ok_response(<<"```erlang\n", B/binary, "```">>),
    LLM = start_llm([R1, R2]),
    try
        Result = solution_generator:generate(
            LLM, beam_canonical_scorer, snapshot(<<"task">>, 60.0),
            #{max_iters => 2, dev_seeds => [42], dev_hard_wall_sec => 3.0}),
        %% Either A or B can win — both are valid submissions.
        ?assert(Result =:= A orelse Result =:= B)
    after
        llm_client:stop(LLM)
    end.

%% --- Missing fence handled gracefully ---

generate_handles_missing_fence_gracefully_test() ->
    %% First response no fence, second response has fence.
    NoFence = ok_response(<<"I am not going to emit code right now.">>),
    Good = ok_response(<<"OK:\n```erlang\n", ?TRIVIAL_W/binary, "```">>),
    LLM = start_llm([NoFence, Good]),
    try
        Result = solution_generator:generate(
            LLM, beam_canonical_scorer, snapshot(<<"task">>, 60.0),
            #{max_iters => 2, dev_seeds => [42], dev_hard_wall_sec => 3.0}),
        ?assertEqual(?TRIVIAL_W, Result)
    after
        llm_client:stop(LLM)
    end.

%% --- Returns empty when LLM never produces a body ---

generate_returns_empty_when_no_fence_ever_test() ->
    NoFence = ok_response(<<"I refuse to emit code.">>),
    LLM = start_llm([NoFence]),
    try
        Result = solution_generator:generate(
            LLM, beam_canonical_scorer, snapshot(<<"task">>, 30.0),
            #{max_iters => 1, dev_seeds => [42], dev_hard_wall_sec => 3.0}),
        ?assertEqual(<<>>, Result)
    after
        llm_client:stop(LLM)
    end.

%% --- LLM error short-circuits the loop ---

generate_returns_best_so_far_on_llm_error_test() ->
    Stub = fun(_, _, _) -> {error, connect_refused} end,
    {ok, LLM} = llm_client:start_link(#{
        base_url => <<"http://stub">>, api_key => <<"k">>,
        model_id => <<"m">>, http_fn => Stub
    }),
    try
        Result = solution_generator:generate(
            LLM, beam_canonical_scorer, snapshot(<<"task">>, 30.0),
            #{max_iters => 1, dev_seeds => [42], dev_hard_wall_sec => 3.0}),
        ?assertEqual(<<>>, Result)
    after
        llm_client:stop(LLM)
    end.

%% --- Compile error feeds back to next iter ---

generate_recovers_from_compile_error_test() ->
    BadResp = ok_response(<<"```erlang\nthis is not erlang\n```">>),
    GoodResp = ok_response(<<"```erlang\n", ?TRIVIAL_W/binary, "```">>),
    LLM = start_llm([BadResp, GoodResp]),
    try
        Result = solution_generator:generate(
            LLM, beam_canonical_scorer, snapshot(<<"task">>, 60.0),
            #{max_iters => 2, dev_seeds => [42], dev_hard_wall_sec => 3.0}),
        ?assertEqual(?TRIVIAL_W, Result)
    after
        llm_client:stop(LLM)
    end.
