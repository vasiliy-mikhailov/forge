%% @doc CLI entry. Wires environment variables → #env{} + #bench_config{}
%% and runs bench/2.
%%
%% Environment:
%%   VLLM_BASE_URL    default "http://localhost:8000"
%%   VLLM_API_KEY     required (used by llm_client)
%%   VLLM_MODEL_ID    default "qwen3.6-27b-awq"
%%   MAX_ITERS        default "1"
%%   HARD_WALL_SEC    default "60.0"
%%   SKILL_PATH       default "tasks/2048/SKILL_tier1.md"
-module(bench_main).
-export([main/1, run/0]).

-include("records.hrl").

-spec main([string()]) -> ok.
main(_Args) ->
    run().

-spec run() -> ok.
run() ->
    {ok, _} = application:ensure_all_started(hackney),
    BaseUrl = list_to_binary(os:getenv("VLLM_BASE_URL", "http://localhost:8000")),
    ApiKey  = list_to_binary(getenv_required("VLLM_API_KEY")),
    ModelId = list_to_binary(os:getenv("VLLM_MODEL_ID", "qwen3.6-27b-awq")),
    MaxIters = list_to_integer(os:getenv("MAX_ITERS", "1")),
    HardWallSec = parse_float(os:getenv("HARD_WALL_SEC", "60.0")),
    SkillPath = os:getenv("SKILL_PATH", "tasks/2048/SKILL_tier1.md"),
    SkillBin = read_skill(SkillPath),
    EnvSpec = compose_env_spec:compose(SkillBin, HardWallSec),

    {ok, LLM} = llm_client:start_link(#{
        base_url => BaseUrl,
        api_key  => ApiKey,
        model_id => ModelId
    }),

    Env = #env{
        canonical_scorer = beam_canonical_scorer,
        model_client     = LLM,
        env_spec         = EnvSpec
    },
    Cfg = #bench_config{
        max_iters     = MaxIters,
        hard_wall_sec = HardWallSec
    },

    Sub = bench:bench(Env, Cfg),

    io:format("~ts~n", [jsx:encode(#{
        <<"score">>        => Sub#submission.score,
        <<"walltime_sec">> => Sub#submission.walltime_sec,
        <<"body_len">>     => byte_size(Sub#submission.body),
        <<"max_iters">>    => MaxIters,
        <<"hard_wall_sec">> => HardWallSec
    }, [{indent, 2}])]),

    llm_client:stop(LLM),
    ok.

%% =====================================================================
%% Private

getenv_required(Key) ->
    case os:getenv(Key) of
        false ->
            io:format(standard_error,
                "error: ~s must be set in the environment~n", [Key]),
            halt(2);
        V -> V
    end.

parse_float(S) ->
    case string:to_float(S) of
        {F, _} when is_float(F) -> F;
        _ ->
            case string:to_integer(S) of
                {I, _} when is_integer(I) -> float(I);
                _ -> 60.0
            end
    end.

read_skill(Path) ->
    case file:read_file(Path) of
        {ok, B} -> B;
        {error, enoent} ->
            io:format(standard_error,
                "warning: SKILL file ~s not found; using placeholder~n",
                [Path]),
            <<"Write an Erlang submission module exporting move/1.\n">>
    end.
