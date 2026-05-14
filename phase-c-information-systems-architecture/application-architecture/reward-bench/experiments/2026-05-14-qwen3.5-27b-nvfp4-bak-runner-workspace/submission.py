from __future__ import annotations
import copy
import random
from transitions import Machine

class Solver:
    """FSM-based 2048 solver using transitions library."""
    
    def __init__(self):
        # Define states
        states = ['building', 'consolidating', 'endgame', 'desperate']
        
        # Define transitions
        transitions_list = [
            {'trigger': 'to_consolidating', 'source': 'building', 'dest': 'consolidating'},
            {'trigger': 'to_building', 'source': 'consolidating', 'dest': 'building'},
            {'trigger': 'to_endgame', 'source': 'consolidating', 'dest': 'endgame'},
            {'trigger': 'to_endgame', 'source': 'building', 'dest': 'endgame'},
            {'trigger': 'to_desperate', 'source': 'endgame', 'dest': 'desperate'},
            {'trigger': 'to_desperate', 'source': 'building', 'dest': 'desperate'},
            {'trigger': 'to_desperate', 'source': 'consolidating', 'dest': 'desperate'},
            {'trigger': 'to_building', 'source': 'desperate', 'dest': 'building'},
        ]
        
        # Create the machine - state will be added to self
        self.machine = Machine(
            model=self,
            states=states,
            initial='building',
            transitions=transitions_list
        )
        
        # Random for any needed randomness (seeded for determinism)
        self.rng = random.Random(42)
    
    def _get_max_tile(self, board: list[list[int]]) -> int:
        """Get maximum tile value on board."""
        return max(max(row) for row in board)
    
    def _count_empty(self, board: list[list[int]]) -> int:
        """Count empty cells."""
        return sum(1 for row in board for cell in row if cell == 0)
    
    def _simulate_move(self, board: list[list[int]], action: str) -> tuple[list[list[int]], bool, int]:
        """Simulate a move and return (new_board, changed, gain)."""
        new_board = copy.deepcopy(board)
        
        if action == 'A':  # Left
            new_board, gain, changed = self._move_left(new_board)
        elif action == 'D':  # Right
            new_board, gain, changed = self._move_right(new_board)
        elif action == 'W':  # Up
            new_board, gain, changed = self._move_up(new_board)
        elif action == 'S':  # Down
            new_board, gain, changed = self._move_down(new_board)
        else:
            return new_board, False, 0
            
        return new_board, changed, gain
    
    def _compress_and_merge_row_left(self, row):
        """Compress and merge a row to the left."""
        n = len(row)
        tiles = [x for x in row if x != 0]
        gained = 0
        merged = []
        i = 0
        while i < len(tiles):
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                v = tiles[i] * 2
                gained += v
                merged.append(v)
                i += 2
            else:
                merged.append(tiles[i])
                i += 1
        merged += [0] * (n - len(merged))
        changed = merged != row
        return merged, gained, changed
    
    def _move_left(self, board):
        changed_any = False
        total_gain = 0
        new_board = []
        for row in board:
            new_row, gained, changed = self._compress_and_merge_row_left(row)
            new_board.append(new_row)
            total_gain += gained
            changed_any = changed_any or changed
        return new_board, total_gain, changed_any
    
    def _move_right(self, board):
        changed_any = False
        total_gain = 0
        new_board = []
        for row in board:
            rev = list(reversed(row))
            new_rev, gained, changed = self._compress_and_merge_row_left(rev)
            new_board.append(list(reversed(new_rev)))
            total_gain += gained
            changed_any = changed_any or changed
        return new_board, total_gain, changed_any
    
    def _transpose(self, board):
        return [list(row) for row in zip(*board)]
    
    def _move_up(self, board):
        t = self._transpose(board)
        moved, gain, changed = self._move_left(t)
        return self._transpose(moved), gain, changed
    
    def _move_down(self, board):
        t = self._transpose(board)
        moved, gain, changed = self._move_right(t)
        return self._transpose(moved), gain, changed
    
    def _heuristic(self, board: list[list[int]]) -> float:
        """
        Heuristic function for board evaluation.
        Balanced approach with emphasis on empty cells and smoothness.
        """
        score = 0
        
        # Empty cells bonus (most important for survival)
        empty = self._count_empty(board)
        score += empty * 1200
        
        # Weight matrix for top-left corner strategy
        weights = [
            [32, 16, 8, 4],
            [16, 8, 4, 2],
            [8, 4, 2, 1],
            [4, 2, 1, 1]
        ]
        
        # Weighted score
        for r in range(4):
            for c in range(4):
                if board[r][c] > 0:
                    score += board[r][c] * weights[r][c]
        
        # Smoothness: reward adjacent equal tiles (potential merges)
        smoothness = 0
        for r in range(4):
            for c in range(4):
                if board[r][c] > 0:
                    for dr, dc in [(0, 1), (1, 0)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 4 and 0 <= nc < 4:
                            if board[nr][nc] == board[r][c]:
                                smoothness += board[r][c] * 6
                            elif board[nr][nc] > 0:
                                ratio = max(board[r][c], board[nr][nc]) / min(board[r][c], board[nr][nc])
                                if ratio > 4:
                                    smoothness -= (ratio - 4) * 18
        
        score += smoothness
        
        # Monotonicity bonus for top-left corner
        monotonic_bonus = 0
        if board[0][0] >= board[0][1] >= board[0][2] >= board[0][3]:
            monotonic_bonus += 180
        if board[0][0] >= board[1][0] >= board[2][0] >= board[3][0]:
            monotonic_bonus += 180
        
        # Bonus for largest tile in corner
        max_val = self._get_max_tile(board)
        if board[0][0] == max_val:
            monotonic_bonus += 180
        elif board[0][1] == max_val or board[1][0] == max_val:
            monotonic_bonus += 90
        
        score += monotonic_bonus
        
        # Penalize isolated high tiles
        isolation_penalty = 0
        for r in range(4):
            for c in range(4):
                if board[r][c] > 32:
                    neighbors = []
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 4 and 0 <= nc < 4:
                            neighbors.append(board[nr][nc])
                    non_zero_neighbors = [n for n in neighbors if n > 0]
                    if len(non_zero_neighbors) == 0:
                        isolation_penalty -= 50
                    elif all(n < board[r][c] // 4 for n in non_zero_neighbors):
                        isolation_penalty -= 25
        
        score += isolation_penalty
        
        return score
    
    def _score_move(self, board: list[list[int]], action: str, depth: int = 0) -> float:
        """Score a move based on heuristic with limited lookahead."""
        new_board, changed, gain = self._simulate_move(board, action)
        if not changed:
            return -1000000
        
        # Score based on resulting board state
        score = self._heuristic(new_board)
        
        # Bonus for merges (gain)
        score += gain * 100
        
        # Lookahead (depth-limited)
        if depth < 1:
            best_future = -float('inf')
            for next_action in ['A', 'W', 'D', 'S']:
                future_score = self._score_move(new_board, next_action, depth + 1)
                best_future = max(best_future, future_score)
            score += best_future * 0.25
        
        return score
    
    def _evaluate_state(self, board: list[list[int]]) -> str:
        """Evaluate current state and determine which FSM state we should be in."""
        max_tile = self._get_max_tile(board)
        empty = self._count_empty(board)
        
        # Check if board is full with no merges possible
        if empty == 0:
            # Check if any merge is possible
            for r in range(4):
                for c in range(3):
                    if board[r][c] == board[r][c+1]:
                        return 'building'
                for c in range(4):
                    if r < 3 and board[r][c] == board[r+1][c]:
                        return 'building'
            return 'desperate'
        
        if empty <= 2:
            return 'desperate'
        
        if max_tile >= 1024:
            return 'endgame'
        elif max_tile >= 512:
            return 'consolidating'
        else:
            return 'building'
    
    def _update_state(self, board: list[list[int]]):
        """Update FSM state based on board conditions."""
        target_state = self._evaluate_state(board)
        current_state = self.state  # transitions adds state attribute to self
        
        if target_state != current_state:
            # Try to transition to target state
            if hasattr(self, f'to_{target_state}'):
                try:
                    getattr(self, f'to_{target_state}')()
                except:
                    pass  # Transition not allowed, stay in current state
    
    def _policy_building(self, board: list[list[int]]) -> str:
        """Policy for building state - focus on creating high tiles."""
        best_action = 'A'
        best_score = float('-inf')
        
        for action in ['A', 'W', 'D', 'S']:
            score = self._score_move(board, action)
            if score > best_score:
                best_score = score
                best_action = action
        
        return best_action
    
    def _policy_consolidating(self, board: list[list[int]]) -> str:
        """Policy for consolidating state - protect high tiles."""
        best_action = 'A'
        best_score = float('-inf')
        
        for action in ['A', 'W', 'S', 'D']:
            score = self._score_move(board, action)
            if score > best_score:
                best_score = score
                best_action = action
        
        return best_action
    
    def _policy_endgame(self, board: list[list[int]]) -> str:
        """Policy for endgame - carefully place tiles to reach 2048."""
        best_action = 'A'
        best_score = float('-inf')
        
        for action in ['A', 'W', 'S', 'D']:
            score = self._score_move(board, action)
            if score > best_score:
                best_score = score
                best_action = action
        
        return best_action
    
    def _policy_desperate(self, board: list[list[int]]) -> str:
        """Policy for desperate state - any move that changes the board."""
        best_action = 'A'
        best_score = float('-inf')
        
        for action in ['A', 'W', 'D', 'S']:
            new_board, changed, gain = self._simulate_move(board, action)
            if changed:
                # In desperate mode, just want any valid move
                score = gain + self._count_empty(new_board) * 10
                if score > best_score:
                    best_score = score
                    best_action = action
        
        return best_action
    
    def move(self, board: list[list[int]]) -> str:
        """
        Decide the next move based on current FSM state.
        
        Args:
            board: 4x4 board as list of lists of integers
            
        Returns:
            One of 'W', 'A', 'S', 'D'
        """
        # Update state based on current board
        self._update_state(board)
        
        # Get policy based on current state
        state = self.state  # transitions adds state attribute to self
        
        if state == 'building':
            return self._policy_building(board)
        elif state == 'consolidating':
            return self._policy_consolidating(board)
        elif state == 'endgame':
            return self._policy_endgame(board)
        elif state == 'desperate':
            return self._policy_desperate(board)
        else:
            return 'A'  # Fallback