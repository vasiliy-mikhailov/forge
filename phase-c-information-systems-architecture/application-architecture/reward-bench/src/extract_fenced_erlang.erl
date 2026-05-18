%% @doc §4 boundary helper — extract the last fenced erlang block
%% from an LLM response.
%%
%% Recognises ```erlang ... ```, ```erl ... ```, and untagged
%% ``` ... ``` fences. When multiple blocks are present, returns
%% the body of the LAST one — agents often show iterations before
%% the final answer.
%%
%% `extract/2' takes an optional anchor: the last block whose body
%% contains that binary wins; falls back to the last block when no
%% block matches. Used by callers that know the final submission
%% shape (e.g. `<<"-module(submission)">>` for the 2048 task).
%%
%% Returns `<<>>` when no fenced block exists at all.
-module(extract_fenced_erlang).

-export([extract/1, extract/2]).

-define(FENCE_RE, "```[ \\t]*(?:erlang|erl)?[ \\t]*\\n(.*?)```").

-spec extract(binary()) -> binary().
extract(Msg) ->
    extract(Msg, undefined).

-spec extract(binary(), binary() | undefined) -> binary().
extract(Msg, PreferContains) ->
    case re:run(Msg, ?FENCE_RE,
                [dotall, {capture, all_but_first, binary}, global]) of
        nomatch ->
            <<>>;
        {match, Groups} ->
            Bodies = [B || [B] <- Groups],
            pick(Bodies, PreferContains)
    end.

-spec pick([binary()], binary() | undefined) -> binary().
pick(Bodies, undefined) ->
    lists:last(Bodies);
pick(Bodies, Anchor) ->
    Preferred = [B || B <- Bodies, binary:match(B, Anchor) =/= nomatch],
    case Preferred of
        []    -> lists:last(Bodies);
        _List -> lists:last(Preferred)
    end.
