from agent import Agent
from oxono import Game, State

import time
import random

class AlphaBetaAgent(Agent):
    def __init__(self, player):
        super().__init__(player)
        self.max_depth = 5

    def act(self, state,remaining_time):
        """
        Choose and return an action for the current turn,
        following the minimax algorithm with alpha-beta pruning. 
        If time is running out, return a random legal action.

        Parameters
        ----------
        state : State
            The current game state.
        remaining_time : float
            Total seconds remaining on your clock for the rest of the game.

        Returns
        -------
        best_action : tuple
            The best action to play in the current state, or a random legal action if time is running out.
        """
        if remaining_time <= 5:
            return random.choice(list(Game.actions(state)))
        
        # best first move when starting as player 0
        if self.player == 0 and state.pieces_x[0] == 8 and state.pieces_o[0] == 8:
            return ('O', (3, 2), (4, 2))
        
        # early turns get more time, late turns less
        turns_played = 16 - (state.pieces_x[self.player] + state.pieces_o[self.player]) #number of turns already played by the agent
        decay = 1.5 
        nrem = max(17 - turns_played, 1) #number of turns remaining for the agent (36 total places, + 2 totems, 17 per player)
        time_limit = remaining_time* (1 - decay**(-1))/ (1 - decay**(-nrem))
        deadline = time.time() + time_limit
        
        _, best_action = self.max_value(state, self.max_depth, float('-inf'), float('inf'), deadline)

        if best_action is None: #time ran out during the search
            return random.choice(list(Game.actions(state)))
        
        return best_action
    
    def max_value(self, state, depth, alpha, beta, deadline):
        """
        Max-value function for minimax with alpha-beta pruning.

        Parameters
        ----------
        state : State
            The current game state.
        depth : int
            The maximum depth to search.
        alpha : float
            The alpha value for alpha-beta pruning.
        beta : float
            The beta value for alpha-beta pruning.
        deadline : float
            The max time by which the function must return to avoid losing the game to timeout.

        Returns
        -------
        max_v, best_action : int, tuple
            The best action and its value to play in the current state, or a random legal action if time is running out.
        """
        if time.time() >= deadline:
            return None, None
        
        if depth == 0 or Game.is_terminal(state):
            if Game.is_terminal(state):
                return Game.utility(state, self.player), None
            else: return self.evaluate(state), None
            
        max_v = float('-inf')
        best_action = None
        
        for action in Game.actions(state):
            if time.time() >= deadline:
                break
            
            new_state = state.copy()
            Game.apply(new_state, action)
            
            v,_ = self.min_value(new_state, depth - 1, alpha, beta, deadline)
            
            if v is None: #time ran out during the recursive call
                break 
            
            if v > max_v:
                max_v = v
                best_action = action
            
            alpha = max(alpha, max_v)
            if beta <= alpha:
                break
        
        if best_action is None and max_v == float('-inf'):
            return None, None
        
        return max_v, best_action
    
    def min_value(self, state, depth, alpha, beta, deadline):
        """
        Min-value function for minimax with alpha-beta pruning.

        Parameters
        ----------
        state : State
            The current game state.
        depth : int
            The maximum depth to search.
        alpha : float
            The alpha value for alpha-beta pruning.
        beta : float
            The beta value for alpha-beta pruning.
        deadline : float
            The max time by which the function must return to avoid losing the game to timeout.

        Returns
        -------
        min_v, best_action : int, tuple
            The best action and its value to play in the current state, or a random legal action if time is running out.
        """
        if time.time() >= deadline:
            return None, None
        
        if depth == 0 or Game.is_terminal(state):
            if Game.is_terminal(state):
                return Game.utility(state, self.player), None
            else: return self.evaluate(state), None
        
        min_v = float('inf')
        best_action = None
        
        for action in Game.actions(state):
            if time.time() >= deadline:
                break
            
            new_state = state.copy()
            Game.apply(new_state, action)
            
            v,_ = self.max_value(new_state, depth - 1, alpha, beta, deadline)
            
            if v is None: #time ran out during the recursive call
                break 
            
            if v < min_v:
                min_v = v
                best_action = action
            
            beta = min(beta, v)
            if beta <= alpha:
                break
        
        if best_action is None and min_v == float('inf'):
            return None, None
        
        return min_v, best_action
    
    def evaluate(self, state):
        """
        Heuristic evaluation function for alpha-beta pruning.

        Parameters
        ----------
        state : State
            The current game state.

        Returns
        -------
        scores sum : int
            The score for the current state.
        """
        opp = 1 - self.player
        
        # Weights for the different criteria of the evaluation function
        A1, A2 = 0.45, 0.35 # 1. Winning potential / threats
        C1, C2 = 0.05, 0.05 # 2.1 big difference in X and 0 pieces
        D1, D2 = 0.10, 0.20 # 2.2 no pieces of one type
        E , F  = 0.05, 0.05 # 3. Totem alignment
        
        # ———————————
        # 1. Winning potential / threats [~ <5] - number of near wins (3 in a row with an open spot)
        my_win = self.near_win_color(state, self.player)
        opp_win = self.near_win_color(state, opp)
        
        sym_win = self.near_win_symbol(state) #if it's the agent's turn, the symbol near wins are an opportunity, otherwise they are a threat
        if (state.current_player == self.player):
            my_win += sym_win
        else:
            opp_win += sym_win
            
        win_score = my_win * A1 - opp_win * A2
        
        # ———————————
        # 2. number of remaining pieces [0; 16]
        my_x = state.pieces_x[self.player]
        my_o = state.pieces_o[self.player]
        opp_x = state.pieces_x[opp]
        opp_o = state.pieces_o[opp]
        
        pieces_score = 0
        
        if (abs(my_x - my_o) > 4 and min(my_x, my_o) < 3): #a big difference in X and O pieces is a disadvantage
            pieces_score -= C1
        if (abs(opp_x - opp_o) > 4 and min(opp_x, opp_o) < 3): #if opp has a big difference in X and O pieces it is an advantage
            pieces_score += C2
        
        if (my_x == 0 or my_o == 0): #no pieces of one type is a disadvantage
            pieces_score -= D1
        if (opp_x == 0 or opp_o == 0): #if opp has no pieces of one type it is an advantage
            pieces_score += D2
        
        # ———————————
        # 3. totem alignment [0;20] - number of new potential placements for totems
        alignment_score = len(Game._totems_actions(state, 'X')) * E + len(Game._totems_actions(state, 'O')) * F
        
        return win_score + pieces_score + alignment_score
    
    def near_win_symbol(self, state):
        """
        Uses the logic of _last_piece_won to count the number of near wins with symbols
        so "+1" if the board has 3 symbols in a row (or XX_X) and an open spot for the 4th
        
        Parameters
        ----------
        state : State
            The current game state.

        Returns
        -------
        score : int
            The number of near wins with symbols for the current state.
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
        Uses the logic of _last_piece_won to count the number of near wins by color for the given player,
        so "+1" if the board has 3 pieces of the same color in a row (or XX_X) and an open spot for the 4th
        
        Parameters
        ----------
        state : State
            The current game state.
        player : str
            The player for whom to count near wins.

        Returns
        -------
        score : int
            The number of near wins by color for the given player in the current state.
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