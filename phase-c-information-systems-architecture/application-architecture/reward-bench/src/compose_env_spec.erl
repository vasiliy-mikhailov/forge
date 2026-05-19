%% @doc §4 env_spec composer. Pure function producing the prompt
%% the LLM sees. Three sections: Task, Output, Budget. The agent
%% doesn't shell out for dev-testing — the orchestrator runs
%% canonical_scorer:score_body on each emission and feeds back
%% scores as the next user message.
-module(compose_env_spec).
-export([compose/2]).

-spec compose(SkillBin :: binary(), BudgetSec :: number()) -> binary().
compose(SkillBin, BudgetSec) ->
    Seconds = trunc(BudgetSec),
    iolist_to_binary([
        "# Task\n\n",
        SkillBin,
        "\n\n# Output\n\n",
        "Emit your final Solver as a fenced ```erlang ... ``` block in "
        "your assistant message. After each emission the harness "
        "compiles your code, plays dev-seed games, and returns scores. "
        "Iterate until you are satisfied; the LAST fenced block is "
        "your submission.\n\n",
        "# Budget\n\n",
        io_lib:format(
            "~B seconds remaining. The harness terminates the "
            "conversation at the deadline.\n", [Seconds])
    ]).
