%% @doc Shared helpers for the fitness-functions/ suite. Pure file-IO
%% over the source tree; no network, no external deps.
-module(fitness_helpers).
-export([src_files/0, read_src/1, src_root/0,
         module_attribute/2, module_exports/1]).

-spec src_root() -> file:filename_all().
src_root() ->
    %% rebar3 eunit runs from the project root; src/ is relative.
    %% This works whether invoked via `make eunit` (host pwd is the
    %% project root, mounted into the dev container as /work) or via
    %% rebar3 directly.
    "src".

-spec src_files() -> [file:filename_all()].
src_files() ->
    Root = src_root(),
    {ok, All} = file:list_dir(Root),
    [filename:join(Root, F)
       || F <- All,
          filename:extension(F) =:= ".erl"].

-spec read_src(file:filename_all()) -> binary().
read_src(Path) ->
    {ok, B} = file:read_file(Path),
    B.

-spec module_attribute(module(), atom()) -> term().
module_attribute(Mod, Key) ->
    Attrs = Mod:module_info(attributes),
    proplists:get_value(Key, Attrs, []).

-spec module_exports(module()) -> [{atom(), arity()}].
module_exports(Mod) ->
    Mod:module_info(exports).
