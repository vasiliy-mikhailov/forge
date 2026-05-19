%% @doc Fitness function — every record declared in records.hrl is
%% referenced by ≥1 src/*.erl module. Catches dead records from
%% refactors.
-module(fitness_records_referenced_tests).
-include_lib("eunit/include/eunit.hrl").

all_records_in_records_hrl_have_users_test() ->
    Hrl = fitness_helpers:read_src("src/records.hrl"),
    {match, Matches} = re:run(Hrl, <<"-record\\((\\w+)">>,
                              [global, {capture, all_but_first, binary}]),
    Records = [R || [R] <- Matches],
    AllSrc = iolist_to_binary(
        [fitness_helpers:read_src(P)
         || P <- fitness_helpers:src_files(),
            filename:basename(P) =/= "records.hrl"]),
    Dead = [R || R <- Records,
                 binary:match(AllSrc,
                              <<"#", R/binary>>) =:= nomatch],
    ?assertEqual([], Dead).
