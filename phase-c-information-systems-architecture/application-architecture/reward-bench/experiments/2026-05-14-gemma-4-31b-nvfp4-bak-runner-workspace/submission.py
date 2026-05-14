from __future__ import annotations
import numpy as np
from transitions import Machine

class Solver:
    def __init__(self):
        # Define states for the FSM
        states = ['building', 'cornering', 'cleaning', 'endgame']
        
        # The Machine requires a model object to hold the state
        self.machine = Machine(model=self, states=states, initial='building')
        
        # Use internal transitions or flexible triggers to avoid MachineError.
        # We'll define transitions that can be triggered from any state if needed,
        # or just use a more robust way to handle state transitions.
        self.transitions = [
            {'trigger': 'reach_64', 'source': 'building', 'dest': 'cornering'},
            {'trigger': 'reach_256', 'source': '*', 'dest': 'cleaning'},
            {'trigger': 'reach_1024', 'source': '*', 'dest': 'endgame'},
        ]
        self.machine.add_transitions(self.transitions)

    def move(self, board: list[list[int]]) -> str:
        # Update state based on the current board
        max_tile = 0
        for row in board:
            for tile in row:
                if tile > max_tile:
                    max_tile = tile
        
        # To avoid MachineError, we check if the trigger is valid for the current state
        # or just use a try-except block.
        try:
            if max_tile >= 1024 and self.state != 'endgame':
                self.trigger('reach_1024')
            elif max_tile >= 256 and self.state not in ['cleaning', 'endgame']:
                self.trigger('reach_256')
            elif max_tile >= 64 and self.state == 'building':
                self.trigger('reach_64')
        except Exception:
            pass

        # Policy based on current state
        if self.state == 'building':
            return self._policy_building(board)
        elif self.state == 'cornering':
            return self._policy_cornering(board)
        elif self.state == 'cleaning':
            return self._policy_cleaning(board)
        elif self.state == 'endgame':
            return self._policy_endgame(board)
        
        return 'D'

    def _policy_building(self, board):
        # Early game: Try to keep tiles moving towards the bottom-right
        return self._get_best_move(board, ['S', 'D', 'A', 'W'])

    def _policy_cornering(self, board):
        # Mid game: Keep largest tile in the bottom-right corner
        return self._get_best_move(board, ['S', 'D', 'A', 'W'])

    def _policy_cleaning(self, board):
        # Late game: Maintain the corner and avoid moving 'Up'
        return self._get_best_move(board, ['S', 'D', 'A', 'W'])

    def _policy_endgame(self, board):
        # High stakes: Extremely careful moves
        return self._get_best_move(board, ['S', 'D', 'A', 'W'])

    def _get_best_move(self, board, priority_list):
        for move in priority_list:
            if self._is_valid_move(board, move):
                return move
        return priority_list[0]

    def _is_valid_move(self, board, move):
        if move == 'A': # Left
            for r in range(4):
                for c in range(3):
                    if board[r][c] == 0 or board[r][c] == board[r][c+1]:
                        return True
        elif move == 'D': # Right
            for r in range(4):
                for c in range(1, 4):
                    if board[r][c] == 0 or board[r][c] == board[r][c-1]:
                        return True
        elif move == 'W': # Up
            for r in range(3):
                for c in range(4):
                    if board[r][c] == 0 or board[r][c] == board[r+1][c]:
                        return True
        elif move == 'S': # Down
            for r in range(1, 4):
                for c in range(4):
                    if board[r][c] == 0 or board[r][c] == board[r-1][c]:
                        return True
        return False