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
import heapq
import math

EMPTY_STEP_COST = 1
FEAR_OF_UNKNOWN = 6.66
UNKNOWN_STEP_COST = EMPTY_STEP_COST * FEAR_OF_UNKNOWN
FEAR_OF_ENEMY = 10
VISITED_STEP_COST = 1

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
        
        action, direction = self.make_decision(can_shoot, holding_flag, position, visible_world)
        print("update: ", action, direction)
        return action, direction

    def get_positions_from_visible_world(self, visible_world, ascii_char):
        positions = []
        rows = [''.join(row) for row in visible_world]
        for row_idx, row in enumerate(rows):
            for col_idx, char in enumerate(row):
                if char == ascii_char:
                    positions.append((row_idx, col_idx))

        return positions

    def update_last_seen_enemy_position(self, visible_world):
        enemy_positions = self.get_positions_from_visible_world(visible_world, ASCII_TILES["blue_agent"])
        if enemy_positions:
            self.knowledge_base["last_seen_enemy_position"] = enemy_positions[0]
        else:
            self.knowledge_base["last_seen_enemy_position"] = None

    def update_enemy_flag_positions(self, visible_world):
        enemy_flag_positions = self.get_positions_from_visible_world(visible_world, ASCII_TILES["blue_flag"])
        self.knowledge_base["enemy_flag_positions"] = enemy_flag_positions

    def update_own_flag_position(self, visible_world):
        own_flag_positions = self.get_positions_from_visible_world(visible_world, ASCII_TILES["red_flag"])
        if own_flag_positions:
            self.knowledge_base["own_flag_position"] = own_flag_positions[0]
        else:
            self.knowledge_base["own_flag_position"] = None

    def make_decision(self, can_shoot, holding_flag, current_position, visible_world):
        print("Knowledge Base:", self.knowledge_base)

        if not any(self.knowledge_base.values()):
            action = "move"
            direction = random.choice(["up", "down", "left", "right"])
        else:
            enemy_flag_positions = self.knowledge_base["enemy_flag_positions"]
            print("Enemy Flag Positions:", enemy_flag_positions)

            if enemy_flag_positions:
                target_position = enemy_flag_positions[0]
                path_found, shortest_path = self.astar(current_position, target_position, visible_world)

                print("Path Found:", path_found)
                print("Shortest Path:", shortest_path)

                if not path_found or len(shortest_path) < 2:
                    # Handle case when no path is found
                    action = "move"
                    direction = random.choice(["up", "down", "left", "right"])
                else:
                    if can_shoot and random.random() > 0.5:
                        action = "shoot"
                        direction = self.get_direction(current_position, shortest_path)
                    else:
                        action = "move"
                        direction = self.get_direction(current_position, shortest_path)
            else:
                # Handle case when enemy_flag_positions is empty
                action = "move"
                direction = random.choice(["up", "down", "left", "right"])

        print("Decision:", action, direction)
        return action, direction


    def determine_direction_towards_enemy(self, current_position, visible_world):
        if self.knowledge_base["last_seen_enemy_position"] is not None:
            enemy_position = self.knowledge_base["last_seen_enemy_position"]
            target_position = self.knowledge_base["own_flag_position"] if enemy_position in self.knowledge_base["enemy_flag_positions"] else enemy_position
            _, shortest_path = self.astar(current_position, target_position, visible_world)
            direction = self.get_direction(current_position, shortest_path)
            return direction

    def determine_direction_towards_flag(self, holding_flag, current_position, visible_world):
        target_position = self.knowledge_base["own_flag_position"] if not holding_flag else random.choice(self.knowledge_base["enemy_flag_positions"])
        _, shortest_path = self.astar(current_position, target_position, visible_world)
        direction = self.get_direction(current_position, shortest_path)
        return direction

    def astar(self, agent_pos, target_pos, visible_world):
        def is_valid(position):
            x, y = position
            return 0 <= x < HEIGHT and 0 <= y < WIDTH
        
        def heuristic(a, b):
            return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)

        def generate_neighbors(pos):
            row, col = pos
            neighbors = [(row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)]
            return [neighbor for neighbor in neighbors if is_valid(neighbor)]

        def cost_from_const(pos, visible_world, came_from):
            x, y = pos
            if visible_world[x][y] == ASCII_TILES["unknown"]:
                return 1
            elif visible_world[x][y] == ASCII_TILES["empty"]:
                return 2
            elif visible_world[x][y] == ASCII_TILES["wall"]:
                return 10000
            elif visible_world[x][y] == ASCII_TILES["red_flag"]:
                return 3

        start = agent_pos
        goal = target_pos
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_cost = {start: 0}

        while open_set:
            _, current_pos = heapq.heappop(open_set)

            neighbors = generate_neighbors(current_pos)

            for neighbor in neighbors:
                cost = cost_from_const(current_pos, visible_world, came_from)
                tentative_g_cost = g_cost[current_pos] + cost
                if neighbor in g_cost and tentative_g_cost >= g_cost[neighbor]:
                    continue
                g_cost[neighbor] = tentative_g_cost
                total_cost = tentative_g_cost + heuristic(neighbor, goal)
                heapq.heappush(open_set, (total_cost, neighbor))
                came_from[neighbor] = current_pos

        return [], [] # Target not reachable

    def get_direction(self, current_pos, shortest_path):
        next_pos = shortest_path[1]
        if next_pos[0] < current_pos[0]:
            return 'up'
        elif next_pos[0] > current_pos[0]:
            return 'down'
        elif next_pos[1] < current_pos[1]:
            return 'left'
        elif next_pos[1] > current_pos[1]:
            return 'right'

    def reconstruct_path(self, came_from, start, goal):
        current = goal
        path = [current]
        while current != start:
            current = came_from[current]
            path.append(current)
        return path[::-1]

    def terminate(self, reason):
        if reason == "died":
            print(self.color, self.index, "died")
