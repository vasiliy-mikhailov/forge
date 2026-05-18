%% @doc EUnit suite for extract_fenced_erlang.
-module(extract_fenced_erlang_tests).
-include_lib("eunit/include/eunit.hrl").

single_erlang_block_returns_body_test() ->
    Msg = <<
        "Here is the solver:\n"
        "```erlang\n"
        "-module(submission).\n"
        "-export([move/1]).\n"
        "move(_) -> w.\n"
        "```\n"
        "Done."
    >>,
    Expected = <<
        "-module(submission).\n"
        "-export([move/1]).\n"
        "move(_) -> w.\n"
    >>,
    ?assertEqual(Expected, extract_fenced_erlang:extract(Msg)).

last_of_multiple_blocks_wins_test() ->
    Msg = <<
        "First:\n```erlang\nFIRST\n```\n"
        "Better:\n```erlang\nSECOND\n```\n"
        "Final:\n```erlang\nTHIRD\n```\n"
    >>,
    ?assertEqual(<<"THIRD\n">>, extract_fenced_erlang:extract(Msg)).

untagged_fence_treated_as_erlang_test() ->
    Msg = <<"```\n-module(x).\n```\n">>,
    ?assertEqual(<<"-module(x).\n">>, extract_fenced_erlang:extract(Msg)).

erl_short_tag_recognised_test() ->
    Msg = <<"```erl\n-module(x).\n```\n">>,
    ?assertEqual(<<"-module(x).\n">>, extract_fenced_erlang:extract(Msg)).

no_fence_returns_empty_binary_test() ->
    ?assertEqual(<<>>, extract_fenced_erlang:extract(<<"no fences here">>)).

prefer_contains_picks_last_block_with_anchor_test() ->
    Msg = <<
        "```erlang\nFOO\n```\n"
        "```erlang\n-module(submission).\n-export([move/1]).\n```\n"
        "```erlang\nBAR\n```\n"
    >>,
    ?assertEqual(
        <<"-module(submission).\n-export([move/1]).\n">>,
        extract_fenced_erlang:extract(Msg, <<"-module(submission)">>)
    ).

prefer_contains_falls_back_to_last_when_no_match_test() ->
    Msg = <<
        "```erlang\nFOO\n```\n"
        "```erlang\nBAR\n```\n"
    >>,
    ?assertEqual(
        <<"BAR\n">>,
        extract_fenced_erlang:extract(Msg, <<"-module(submission)">>)
    ).
