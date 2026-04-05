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


class RandomAgent(Agent):
    def __init__(self, player):
        super().__init__(player)
    
    def act(self, state, remaining_time):
        best_action = None
        best_score = float('-inf')
        for action in Game.actions(state):
            if remaining_time <= 10:
                return random.choice(Game.actions(state))
            new_state = state.copy()
            Game.apply(new_state, action)
            if self.evaluate(new_state) == 10:
                return action
            elif self.evaluate(new_state) > best_score:
                best_score = self.evaluate(new_state)
                best_action = action
        return best_action
    
    def evaluate(self, state):
        if Game._last_piece_won(state):
            return 10
        else:
            return 0
        