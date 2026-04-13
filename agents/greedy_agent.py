from agent import Agent
from oxono import Game, State
import random

class GreedyAgent(Agent):
    def __init__(self, player):
        super().__init__(player)

    def act(self, state, remaining_time):
        """
        Choose and return an action for the current turn.
        The greedy agent looks exactly one step ahead and picks the move
        that maximizes its immediate score.

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
        best_action = None
        max_score = float('-inf')
        
        actions = list(Game.actions(state))
        if not actions:
            return None
                    
        best_action = random.choice(actions)
        
        if remaining_time <= 5:
            return best_action

        for action in actions:
            # Simulate the move
            new_state = state.copy()
            Game.apply(new_state, action)
            
            # 1. Immediate Win Check
            if Game.is_terminal(new_state):
                utility = Game.utility(new_state, self.player)
                if utility > 0:
                    return action # Play the winning move immediately!
                else:
                    continue # Ignore moves that make us lose immediately

            # 2. Evaluation for non-terminal states
            score = self.greedy_evaluation(new_state)
            
            if score > max_score:
                max_score = score
                best_action = action
                
        return best_action

    def greedy_evaluation(self, state):
        """
        A simplified evaluation function. 
        A greedy agent only cares about immediate tangible advantages, 
        mainly setting up its own near-wins and blocking the opponent's.
        
        Parameters
        ----------
        state : State
            The current game state.

        Returns
        -------
        score : int
            The score for the current state.
        """
        opp = 1 - self.player
        
        my_win = self.near_win_color(state, self.player)
        opp_win = self.near_win_color(state, opp)
        
        sym_win = self.near_win_symbol(state)
        if (state.current_player == self.player):
            my_win += sym_win
        else:
            opp_win += sym_win
        
        score = (my_win * 10) - (opp_win * 50) # Heavy penalty for leaving opponent threats
            
        return score

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