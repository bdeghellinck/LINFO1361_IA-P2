from agent import Agent
from oxono import Game, State

import random
"""
GAME FUNCTIONS
Game.to_move(state: State) -> int: 
    Return the index of the player whose turn it is.
Game._totems_actions(state: State, totem: str) -> list[tuple[str, tuple[int, int]]]: 
    Return all valid destination squares for a given Totem
Game.actions(state: State) -> list[tuple[str, tuple[int, int], tuple[int, int]]]:
    Return all legal actions available to the current player.
Game.apply(state: State, action: tuple[str, tuple[int, int], tuple[int, int]]):
    Apply an action to the state, mutating it in place.
Game._last_piece_won(state: State) -> bool:
    Return True if the last piece placed on the board created a winning alignment.
Game.is_terminal(state: State) -> bool:
    Return True if the game is over.
Game.utility(state: State, player: int) -> int:
    Return the utility of a terminal state for the given player.

STATE FUNCTIONS
State.copy(self) -> 'State':
    Return a deep copy of this state.

"""

class AlphaBetaAgent(Agent):
    def __init__(self, player):
        super().__init__(player)
        self.max_depth = 3

    def act(self, state,remaining_time):
        _, best_action = self.max_value(state, self.max_depth, float('-inf'), float('inf'))

        if best_action is None or remaining_time <= 5:
            return random.choice(list(Game.actions(state)))
        
        return best_action
    
    def max_value(self, state, depth, alpha, beta):
        if depth == 0 or Game.is_terminal(state):
            if Game.is_terminal(state):
                return Game.utility(state, self.player), None
            else: return self.evaluate(state), None
            
        max_v = float('-inf')
        best_action = None
        
        for action in Game.actions(state):
            new_state = state.copy()
            Game.apply(new_state, action)
            
            v,_ = self.min_value(new_state, depth - 1, alpha, beta)
            
            if v > max_v:
                max_v = v
                best_action = action
            
            alpha = max(alpha, max_v)
            if beta <= alpha:
                break
        return max_v, best_action
    
    def min_value(self, state, depth, alpha, beta):
        if depth == 0 or Game.is_terminal(state):
            if Game.is_terminal(state):
                return Game.utility(state, self.player), None
            else: return self.evaluate(state), None
        
        min_v = float('inf')
        best_action = None
        
        for action in Game.actions(state):
            new_state = state.copy()
            Game.apply(new_state, action)
            
            v,_ = self.max_value(new_state, depth - 1, alpha, beta)
            
            if v < min_v:
                min_v = v
                best_action = action
            
            beta = min(beta, v)
            if beta <= alpha:
                break
        return min_v, best_action
    
    def evaluate(self, state):
        """
        Heuristic evaluation function
        """
        A1, A2 = 0.40, 0.35
        B = 0.20
        C1, C2 = 0.05, 0.05
        D1, D2 = 0.10, 0.20
        E, F = 0.05, 0.05

        opp = 1 - self.player
        
        # 1. Winning potential / threats [~ <5] - number of near wins (3 in a row)
        my_win = self.near_win_color(state, self.player)
        opp_win = self.near_win_color(state, opp)
        sym_win = self.near_win_symbol(state)
        
        win_score = my_win * A1 - opp_win * A2 + sym_win * B
        
        # 2. number of remaining pieces [0; 16]
        my_x = state.pieces_x[self.player]
        my_o = state.pieces_o[self.player]
        opp_x = state.pieces_x[opp]
        opp_o = state.pieces_o[opp]
        
        pieces_score = 0
        
        if (abs(my_x - my_o) > 4 and min(my_x, my_o) < 3):
            pieces_score -= C1
        if (abs(opp_x - opp_o) > 4 and min(opp_x, opp_o) < 3):
            pieces_score += C2
        
        if (my_x == 0 or my_o == 0):
            pieces_score -= D1
        if (opp_x == 0 or opp_o == 0):
            pieces_score += D2
        
        # 3. totem alignment [0;20] - number of new potential placements for totems
        alignment_score = len(Game._totems_actions(state, 'X')) * E + len(Game._totems_actions(state, 'O')) * F
        
        return win_score + pieces_score + alignment_score
    
    def near_win_symbol(self, state):
        """
        Uses the logic of _last_piece_won to check if the board has 3 symbols in a row and an open spot for the 4th
        """
        board = state.board
        score = 0
        for r in range(6):
            for c in range(6):
                cell = board[r][c]
                if cell is None:
                    continue
                symbol, color = cell

                for dr, dc in [(1, 0), (0, 1)]:
                    count_symbol = 1
                    empty_symbol = 0 #empty cell in symbol streak

                    valid_symbol = True
                    for i in range(1, 4):
                        nr, nc = r + i*dr, c + i*dc
                        if not (0 <= nr < 6 and 0 <= nc < 6):
                            break
                        if board[nr][nc] is None: #allow one empty cell
                            if valid_symbol and empty_symbol == 0: 
                                empty_symbol += 1
                            else:
                                valid_symbol = False
                            
                            if not valid_symbol:
                                break
                        else:   
                            sym, col = board[nr][nc]
                            if sym == symbol and valid_symbol:
                                count_symbol += 1
                            else:
                                valid_symbol = False
                            if not valid_symbol:
                                break
                    
                    valid_symbol = True
                    for i in range(1, 4):
                        nr, nc = r + -i*dr, c + -i*dc
                        if not (0 <= nr < 6 and 0 <= nc < 6):
                            break
                        if board[nr][nc] is None: #allow one empty cell
                            if valid_symbol and empty_symbol == 0: 
                                empty_symbol += 1
                            else:
                                valid_symbol = False
                            
                            if not valid_symbol:
                                break
                        else:   
                            sym, col = board[nr][nc]
                            if sym == symbol and valid_symbol:
                                count_symbol += 1
                            else:
                                valid_symbol = False
                            if not valid_symbol:
                                break

                    if count_symbol == 3 and empty_symbol >= 1:
                        score += 1

        return score
    
    def near_win_color(self, state, player):
        """
        Uses the logic of _last_piece_won to check if the player has 3 color in a row and an open spot for the 4th
        """
        board = state.board
        score = 0
        for r in range(6):
            for c in range(6):
                cell = board[r][c]
                if cell is None:
                    continue
                symbol, color = cell
                if color != player:
                    continue

                for dr, dc in [(1, 0), (0, 1)]:
                    count_color = 1
                    empty_color = 0 #empty cell in color streak

                    valid_color = True
                    for i in range(1, 4):
                        nr, nc = r + i*dr, c + i*dc
                        if not (0 <= nr < 6 and 0 <= nc < 6):
                            break
                        if board[nr][nc] is None: #allow one empty cell
                            if valid_color and empty_color == 0:
                                empty_color += 1
                            else:
                                valid_color = False
                            
                            if not valid_color:
                                break
                        else:
                            sym, col = board[nr][nc]
                            if col == color and valid_color:
                                count_color += 1
                            else:
                                valid_color = False
                            if not valid_color:
                                break
                    
                    valid_color = True
                    for i in range(1, 4):
                        nr, nc = r + -i*dr, c + -i*dc
                        if not (0 <= nr < 6 and 0 <= nc < 6):
                            break
                        if board[nr][nc] is None: #allow one empty cell
                            if valid_color and empty_color == 0:
                                empty_color += 1
                            else:
                                valid_color = False
                            
                            if not valid_color:
                                break
                        else:
                            sym, col = board[nr][nc]
                            if col == color and valid_color:
                                count_color += 1
                            else:
                                valid_color = False
                            if not valid_color:
                                break

                    if count_color == 3 and empty_color >= 1:
                        score += 1

        return score