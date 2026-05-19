%% @doc Plays one 2048 game against a SolverModule per
%% SOLUTION-ARCHITECTURE.md §5.
%%
%% Bounded by three guards:
%%   - HardWallSec wallclock deadline (checked each iter)
%%   - MaxMoves cap on loop iterations
%%   - is_lost / max_tile >= 2048 termination
%%
%% Catches Solver crashes and invalid-action returns; recorded
%% as state=error with the cause in the result record.
-module(runner_canonical).

-export([play_game/4]).

-include("records.hrl").

-define(WIN_TILE, 2048).

-spec play_game(module(), non_neg_integer(), number(), pos_integer()) ->
    #game_result{}.
play_game(SolverModule, Seed, HardWallSec, MaxMoves) ->
    GS = env_2048:new_board(Seed),
    T0 = erlang:monotonic_time(millisecond),
    Deadline = T0 + trunc(HardWallSec * 1000),
    loop(SolverModule, GS, Deadline, MaxMoves, T0, 0).

%% =====================================================================
%% Private

loop(_SolverModule, GS, _Deadline, MaxMoves, T0, Iter)
  when Iter >= MaxMoves ->
    terminate(GS, max_moves_reached, T0);
loop(SolverModule, GS, Deadline, MaxMoves, T0, Iter) ->
    Now = erlang:monotonic_time(millisecond),
    case Now >= Deadline of
        true ->
            terminate(GS, wall_clock_expired, T0);
        false ->
            case env_2048:max_tile(GS) >= ?WIN_TILE of
                true ->
                    terminate(GS, won, T0);
                false ->
                    case env_2048:is_lost(GS) of
                        true ->
                            terminate(GS, lost, T0);
                        false ->
                            take_solver_move(SolverModule, GS, Deadline,
                                             MaxMoves, T0, Iter)
                    end
            end
    end.

take_solver_move(SolverModule, GS, Deadline, MaxMoves, T0, Iter) ->
    try
        Action = SolverModule:move(env_2048:board(GS)),
        case lists:member(Action, [w, a, s, d]) of
            false ->
                terminate_error(GS, {invalid_action, Action}, T0);
            true ->
                {GS1, _Changed} = env_2048:step(GS, Action),
                loop(SolverModule, GS1, Deadline, MaxMoves, T0, Iter + 1)
        end
    catch
        Class:Reason ->
            terminate_error(GS, {Class, Reason}, T0)
    end.

terminate(GS, State, T0) ->
    Now = erlang:monotonic_time(millisecond),
    #game_result{
        score        = env_2048:score(GS),
        max_tile     = env_2048:max_tile(GS),
        moves        = env_2048:moves(GS),
        state        = State,
        walltime_sec = (Now - T0) / 1000.0
    }.

terminate_error(GS, Reason, T0) ->
    R = terminate(GS, error, T0),
    R#game_result{error = Reason}.
