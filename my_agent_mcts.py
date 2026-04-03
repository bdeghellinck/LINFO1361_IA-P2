from agent import Agent
from oxono import Game
import random

class RandomAgent(Agent):
    def __init__(self, player):
        super().__init__(player)
    
    def act(self, state, remaining_time):
        print("Act from alpha beta")
        actions = list(Game.actions(state))
        return random.choice(actions)