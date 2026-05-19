%% @doc LLM client gen_server — wraps hackney calls to a
%% vLLM-compatible /v1/chat/completions endpoint.
%%
%% Config map keys:
%%   base_url        :: binary()  required
%%   api_key         :: binary()  required
%%   model_id        :: binary()  required
%%   temperature     :: float()   default 0.7
%%   connect_timeout :: integer() default 30_000 (ms)
%%   recv_timeout    :: integer() | infinity     default infinity
%%   http_fn         :: optional 3-arg callable for testing; injects
%%                     an HTTP responder. Default forwards to
%%                     hackney with the configured timeouts.
%%
%% LLM endpoints take seconds-to-minutes to generate. Hackney's
%% built-in defaults (8 s connect, 5 s recv) are wrong for this
%% workload — they fire mid-generation. The explicit values
%% above match what production endpoints actually deliver.
-module(llm_client).
-behaviour(gen_server).

-export([start_link/1, chat/2, stop/1]).
-export([init/1, handle_call/3, handle_cast/2,
         handle_info/2, terminate/2, code_change/3]).

-type http_fn() :: fun((Url :: binary(),
                        Headers :: [{binary(), binary()}],
                        Body :: binary()) ->
                            {ok, integer(), binary()} | {error, term()}).

-record(state, {
    base_url    :: binary(),
    api_key     :: binary(),
    model_id    :: binary(),
    temperature :: float(),
    http_fn     :: http_fn()
}).

-spec start_link(map()) -> {ok, pid()} | {error, term()}.
start_link(Config) ->
    gen_server:start_link(?MODULE, Config, []).

-spec chat(pid(), [map()]) -> {ok, binary()} | {error, term()}.
chat(Pid, Messages) ->
    gen_server:call(Pid, {chat, Messages}, infinity).

-spec stop(pid()) -> ok.
stop(Pid) ->
    gen_server:stop(Pid).

%% =====================================================================
%% gen_server callbacks

init(Config) ->
    ConnectTimeout = maps:get(connect_timeout, Config, 30_000),
    RecvTimeout    = maps:get(recv_timeout,    Config, infinity),
    HttpFn = maps:get(
        http_fn, Config,
        fun(Url, Headers, Body) ->
            hackney_post(Url, Headers, Body, ConnectTimeout, RecvTimeout)
        end),
    {ok, #state{
        base_url    = maps:get(base_url,    Config),
        api_key     = maps:get(api_key,     Config),
        model_id    = maps:get(model_id,    Config),
        temperature = maps:get(temperature, Config, 0.7),
        http_fn     = HttpFn
    }}.

handle_call({chat, Messages}, _From, S) ->
    Url = build_url(S#state.base_url),
    Headers = [
        {<<"Authorization">>, <<"Bearer ", (S#state.api_key)/binary>>},
        {<<"Content-Type">>, <<"application/json">>}
    ],
    Body = jsx:encode(#{
        <<"model">>       => S#state.model_id,
        <<"messages">>    => Messages,
        <<"temperature">> => S#state.temperature
    }),
    HttpFn = S#state.http_fn,
    Reply = case HttpFn(Url, Headers, Body) of
        {ok, 200, RespBody}  -> extract_content(RespBody);
        {ok, Status, Resp}    -> {error, {http, Status, Resp}};
        {error, _} = Err      -> Err
    end,
    {reply, Reply, S};
handle_call(_Other, _From, S) ->
    {reply, {error, unknown_call}, S}.

handle_cast(_, S) -> {noreply, S}.
handle_info(_, S) -> {noreply, S}.
terminate(_, _) -> ok.
code_change(_, S, _) -> {ok, S}.

%% =====================================================================
%% Private

build_url(Base) ->
    Trimmed = re:replace(Base, <<"/+$">>, <<>>, [{return, binary}]),
    case re:run(Trimmed, <<"/v1$">>) of
        {match, _} ->
            <<Trimmed/binary, "/chat/completions">>;
        nomatch ->
            <<Trimmed/binary, "/v1/chat/completions">>
    end.

extract_content(RespBody) ->
    try
        Decoded = jsx:decode(RespBody, [return_maps]),
        case Decoded of
            #{<<"choices">> :=
              [#{<<"message">> :=
                 #{<<"content">> := C}} | _]} ->
                {ok, C};
            _ ->
                {error, {decode, no_choices, RespBody}}
        end
    catch
        _:Reason -> {error, {decode, Reason, RespBody}}
    end.

hackney_post(Url, Headers, Body, ConnectTimeout, RecvTimeout) ->
    Opts = [with_body,
            {connect_timeout, ConnectTimeout},
            {recv_timeout,    RecvTimeout}],
    case hackney:post(Url, Headers, Body, Opts) of
        {ok, Status, _RespHeaders, RespBody} -> {ok, Status, RespBody};
        {error, _} = E -> E
    end.
