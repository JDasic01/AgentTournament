# First name Last name

""" 
Description of the agent (approach / strategy / implementation) in short points,
fictional example / ideas:
- It uses the knowledge base to remember:
     - the position where the enemy was last seen,
     - enemy flag positions,
     - the way to its flag.
- I use a machine learning model that, based on what the agent sees around it, decides:
     - in which direction the agent should take a step (or stay in place),
     - whether and in which direction to shoot.
- One agent always stays close to the flag while the other agents are on the attack.
- Agents communicate with each other:
     - position of seen enemies and in which direction they are moving,
     - the position of the enemy flag,
     - agent's own position,
     - agent's own condition (is it still alive, has it taken the enemy's flag, etc.)
- Agents prefer to maintain a distance from each other (not too close and not too far).
- etc...
"""

import random
from config import *

class Agent:
    
    def __init__(self, color, index):
        self.color = color
        self.index = index
        self.knowledge_base = {
            "last_seen_enemy_position": None,
            "enemy_flag_positions": [],
            "own_flag_position": None,
        }

    def update(self, visible_world, position, can_shoot, holding_flag):
        # Update knowledge base based on visible_world and other parameters
        self.update_last_seen_enemy_position(visible_world)
        self.update_enemy_flag_positions(visible_world)
        self.update_own_flag_position(visible_world)
        action, direction = self.make_decision(can_shoot, holding_flag)
        
        return action, direction

    def update_last_seen_enemy_position(self, visible_world):
        # Implement logic to update the last seen enemy position in the knowledge base
        pass

    def update_enemy_flag_positions(self, visible_world):
        # Implement logic to update enemy flag positions in the knowledge base
        pass

    def update_own_flag_position(self, visible_world):
        # Implement logic to update own flag position in the knowledge base
        pass

    def make_decision(self, can_shoot, holding_flag):
        # Implement a more sophisticated decision-making process based on knowledge base
        
        # Example: If an enemy is seen, shoot in its direction
        if self.knowledge_base["last_seen_enemy_position"] is not None and can_shoot:
            action = "shoot"
            direction = self.determine_direction_towards_enemy()
        else:
            # Example: Move towards the enemy flag if not holding the flag
            action = "move"
            direction = self.determine_direction_towards_flag(holding_flag)

        return action, direction

    def determine_direction_towards_enemy(self):
        # Implement logic to determine the direction towards the last seen enemy
        pass

    def determine_direction_towards_flag(self, holding_flag):
        # Implement logic to determine the direction towards the enemy flag or own flag
        pass

    def terminate(self, reason):
        if reason == "died":
            print(self.color, self.index, "died")
