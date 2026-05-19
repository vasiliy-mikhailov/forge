%% @doc EUnit suite for llm_client — uses an injected http_fn
%% stub so no real HTTP traffic. Real-vLLM coverage comes from
%% Common Test in cycle 240.
-module(llm_client_tests).
-include_lib("eunit/include/eunit.hrl").

base_config() ->
    #{
        base_url => <<"http://stub:8000">>,
        api_key  => <<"sk-test">>,
        model_id => <<"qwen3.6-27b-awq">>
    }.

config_with(Extra) ->
    maps:merge(base_config(), Extra).

ok_response(Content) ->
    jsx:encode(#{
        <<"choices">> => [
            #{<<"message">> => #{<<"content">> => Content}}
        ]
    }).

chat_returns_content_on_200_test() ->
    Stub = fun(_Url, _Headers, _Body) ->
        {ok, 200, ok_response(<<"Hello!">>)}
    end,
    {ok, Pid} = llm_client:start_link(config_with(#{http_fn => Stub})),
    try
        ?assertEqual(
            {ok, <<"Hello!">>},
            llm_client:chat(Pid, [#{role => user, content => <<"hi">>}])
        )
    after
        llm_client:stop(Pid)
    end.

chat_returns_error_on_non_200_test() ->
    Stub = fun(_, _, _) -> {ok, 401, <<"unauthorized">>} end,
    {ok, Pid} = llm_client:start_link(config_with(#{http_fn => Stub})),
    try
        ?assertMatch({error, {http, 401, _}}, llm_client:chat(Pid, []))
    after
        llm_client:stop(Pid)
    end.

chat_returns_error_on_http_failure_test() ->
    Stub = fun(_, _, _) -> {error, connect_refused} end,
    {ok, Pid} = llm_client:start_link(config_with(#{http_fn => Stub})),
    try
        ?assertEqual({error, connect_refused}, llm_client:chat(Pid, []))
    after
        llm_client:stop(Pid)
    end.

chat_returns_error_on_malformed_response_test() ->
    Stub = fun(_, _, _) -> {ok, 200, <<"not json at all">>} end,
    {ok, Pid} = llm_client:start_link(config_with(#{http_fn => Stub})),
    try
        ?assertMatch({error, {decode, _, _}}, llm_client:chat(Pid, []))
    after
        llm_client:stop(Pid)
    end.

chat_returns_error_when_response_lacks_choices_test() ->
    Resp = jsx:encode(#{<<"id">> => <<"abc">>}),
    Stub = fun(_, _, _) -> {ok, 200, Resp} end,
    {ok, Pid} = llm_client:start_link(config_with(#{http_fn => Stub})),
    try
        ?assertMatch({error, {decode, no_choices, _}},
                     llm_client:chat(Pid, []))
    after
        llm_client:stop(Pid)
    end.

http_fn_receives_authorization_header_test() ->
    Self = self(),
    Stub = fun(_Url, Headers, _Body) ->
        Self ! {headers_captured, Headers},
        {ok, 200, ok_response(<<"x">>)}
    end,
    {ok, Pid} = llm_client:start_link(config_with(#{http_fn => Stub})),
    try
        {ok, _} = llm_client:chat(Pid, []),
        Headers = receive {headers_captured, H} -> H
                  after 1000 -> ?assert(false), []
                  end,
        AuthHeader = proplists:get_value(<<"Authorization">>, Headers),
        ?assertEqual(<<"Bearer sk-test">>, AuthHeader)
    after
        llm_client:stop(Pid)
    end.

http_fn_receives_url_with_v1_chat_completions_suffix_test() ->
    Self = self(),
    Stub = fun(Url, _Headers, _Body) ->
        Self ! {url_captured, Url},
        {ok, 200, ok_response(<<"x">>)}
    end,
    {ok, Pid} = llm_client:start_link(config_with(#{http_fn => Stub})),
    try
        {ok, _} = llm_client:chat(Pid, []),
        Url = receive {url_captured, U} -> U
              after 1000 -> ?assert(false), <<>>
              end,
        ?assertEqual(<<"http://stub:8000/v1/chat/completions">>, Url)
    after
        llm_client:stop(Pid)
    end.

base_url_already_with_v1_does_not_double_append_test() ->
    Self = self(),
    Stub = fun(Url, _, _) ->
        Self ! {url, Url},
        {ok, 200, ok_response(<<"x">>)}
    end,
    Cfg = config_with(#{
        base_url => <<"http://stub:8000/v1">>,
        http_fn  => Stub
    }),
    {ok, Pid} = llm_client:start_link(Cfg),
    try
        {ok, _} = llm_client:chat(Pid, []),
        Url = receive {url, U} -> U
              after 1000 -> ?assert(false), <<>>
              end,
        ?assertEqual(<<"http://stub:8000/v1/chat/completions">>, Url)
    after
        llm_client:stop(Pid)
    end.
