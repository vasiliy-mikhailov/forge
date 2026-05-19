%% @doc Behaviour for canonical scoring. §2 / §5 of
%% SOLUTION-ARCHITECTURE.md. Implementations:
%%   beam_canonical_scorer  (production; in-VM compile + load + run)
%%   fake_canonical_scorer  (test; scripted results)
-module(canonical_scorer).

-include("records.hrl").

-callback score_body(BodyBin   :: binary(),
                     Seeds     :: [non_neg_integer()],
                     HardWallSec :: number()) ->
    #attempt_result{}.

-export([score_body/4]).

-spec score_body(module(), binary(), [non_neg_integer()], number()) ->
    #attempt_result{}.
score_body(Module, BodyBin, Seeds, HardWallSec) ->
    Module:score_body(BodyBin, Seeds, HardWallSec).
