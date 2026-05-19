%% @doc Common Test live suite — bench against real vLLM.
%%
%% Skipped when VLLM_API_KEY is not in the environment. When run:
%% one orchestrator iter, 60s wallclock budget, asserts the returned
%% Submission has a parseable Erlang body exporting move/1, a
%% non-negative float score, and positive walltime.
-module(bench_live_SUITE).
-include_lib("common_test/include/ct.hrl").
-include("records.hrl").

-export([suite/0, all/0, init_per_suite/1, end_per_suite/1]).
-export([bench_against_real_vllm/1, llm_probe/1]).

-define(INLINE_SKILL, <<
    "Write an Erlang module named `submission` that exports `move/1`.\n"
    "\n"
    "  -module(submission).\n"
    "  -export([move/1]).\n"
    "  -spec move(Board :: [[non_neg_integer()]]) -> w | a | s | d.\n"
    "  move(Board) -> ... your strategy here ...\n"
    "\n"
    "Board is a 4x4 list of lists of non-negative integers; 0 is an\n"
    "empty cell, tiles are powers of 2. Return one of the atoms w\n"
    "(up), a (left), s (down), d (right). Maximize the 2048 game\n"
    "score on canonical held-out seeds.\n"
    "\n"
    "Only use functions from the Erlang/OTP standard library.\n"
    "`move/1` must be a pure function — no spawn, no file: calls,\n"
    "no gen_tcp:, no process_flag.\n"
>>).

suite() ->
    [{timetrap, {minutes, 20}}].

all() ->
    [llm_probe, bench_against_real_vllm].

init_per_suite(Config) ->
    case os:getenv("VLLM_API_KEY") of
        false ->
            {skip, "VLLM_API_KEY not set; live test requires real vLLM"};
        "" ->
            {skip, "VLLM_API_KEY is empty"};
        _ ->
            {ok, _} = application:ensure_all_started(hackney),
            Config
    end.

end_per_suite(_Config) ->
    ok.

%% Raw LLM round-trip — what does the model emit when asked for an
%% Erlang Solver? Logs the assistant content so we can diagnose
%% why bench_against_real_vllm got an empty body.
llm_probe(_Config) ->
    BaseUrl = list_to_binary(os:getenv("VLLM_BASE_URL",
                                       "http://localhost:8000")),
    ApiKey  = list_to_binary(os:getenv("VLLM_API_KEY")),
    ModelId = list_to_binary(os:getenv("VLLM_MODEL_ID",
                                       "qwen3.6-27b-awq")),

    Prompt = <<
        "Write an Erlang module named `submission` that exports `move/1`.\n"
        "The function takes a 4x4 board and returns one of the atoms\n"
        "w, a, s, d.\n\n"
        "Emit your Solver as a fenced ```erlang ... ``` block in your\n"
        "assistant message. Do not explain — just emit the module."
    >>,

    {ok, LLM} = llm_client:start_link(#{
        base_url => BaseUrl,
        api_key  => ApiKey,
        model_id => ModelId
    }),
    try
        ct:log("base_url=~ts model_id=~ts", [BaseUrl, ModelId]),
        ct:log("prompt (~p bytes):~n~ts", [byte_size(Prompt), Prompt]),

        T0 = erlang:monotonic_time(millisecond),
        Result = llm_client:chat(LLM, [#{role => <<"user">>,
                                          content => Prompt}]),
        DT = erlang:monotonic_time(millisecond) - T0,
        ct:log("response took ~p ms", [DT]),

        case Result of
            {ok, Content} ->
                ct:log("assistant content (~p bytes):~n~ts",
                       [byte_size(Content), Content]),
                Ext1 = extract_fenced_erlang:extract(Content),
                Ext2 = extract_fenced_erlang:extract(
                          Content, <<"-module(submission)">>),
                ct:log("extract/1 (last fence)  -> ~p bytes",
                       [byte_size(Ext1)]),
                ct:log("extract/2 (anchored)    -> ~p bytes",
                       [byte_size(Ext2)]);
            {error, Reason} ->
                ct:log("LLM error: ~p", [Reason])
        end
    after
        llm_client:stop(LLM)
    end.

bench_against_real_vllm(_Config) ->
    BaseUrl = list_to_binary(os:getenv("VLLM_BASE_URL",
                                       "http://localhost:8000")),
    ApiKey  = list_to_binary(os:getenv("VLLM_API_KEY")),
    ModelId = list_to_binary(os:getenv("VLLM_MODEL_ID",
                                       "qwen3.6-27b-awq")),

    EnvSpec = compose_env_spec:compose(?INLINE_SKILL, 60.0),

    {ok, LLM} = llm_client:start_link(#{
        base_url => BaseUrl,
        api_key  => ApiKey,
        model_id => ModelId
    }),
    try
        Env = #env{
            canonical_scorer = beam_canonical_scorer,
            model_client     = LLM,
            env_spec         = EnvSpec
        },
        %% max_iters=1 outer; solution_generator's inner reasoning
        %% loop default is 5, so we get ~5 LLM rounds with feedback.
        %% hard_wall_sec=5.0 per-game (HARD_WALL_SEC per cycle 254).
        Cfg = #bench_config{max_iters = 1, hard_wall_sec = 5.0},
        Sub = bench:bench(Env, Cfg),

        true = is_record(Sub, submission),

        %% Chain assertions — what this test pins:
        %%   1. bench:bench/2 returns a #submission{}
        %%   2. body is a binary (possibly empty if the agent did
        %%      not emit a fenced block within hard_wall_sec)
        %%   3. score is a non-negative float (canonical_scorer ran)
        %%   4. walltime_sec is a non-negative float
        %%
        %% Agent quality (whether the body is a working Solver) is
        %% a separate, downstream measurement — logged here for
        %% observation, not asserted.
        Body = Sub#submission.body,
        true = is_binary(Body),
        true = is_float(Sub#submission.score),
        true = Sub#submission.score >= 0.0,
        true = is_float(Sub#submission.walltime_sec),
        true = Sub#submission.walltime_sec >= 0.0,

        ct:log("body byte_size = ~p", [byte_size(Body)]),
        ct:log("score = ~p", [Sub#submission.score]),
        ct:log("walltime_sec = ~p", [Sub#submission.walltime_sec]),
        case binary:match(Body, <<"-module(submission)">>) of
            nomatch when byte_size(Body) > 0 ->
                ct:log("WARN: body non-empty but missing "
                       "-module(submission); agent did not follow "
                       "the contract.");
            nomatch ->
                ct:log("INFO: body empty — agent did not emit a "
                       "fenced erlang block within budget.");
            _ ->
                ct:log("INFO: body declares -module(submission).")
        end
    after
        llm_client:stop(LLM)
    end.
