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


from config import *
import random
import json
import heapq
import math

EMPTY_STEP_COST = 1
FEAR_OF_UNKNOWN = 6.66
UNKNOWN_STEP_COST = EMPTY_STEP_COST * FEAR_OF_UNKNOWN
FEAR_OF_ENEMY = 10
VISITED_STEP_COST = 1

ENEMY = "blue"
MY = "red"
MEMORY_FILE = MY + "_knowledge_base.json"

class Agent:
    
    def __init__(self, color, index):
        self.color = color
        self.index = index
        self.knowledge_base = {
            "enemy_agent_positions": [],
            "enemy_flag_position": [],
            "my_flag_position": [],
            "world_knowledge": [[ASCII_TILES["unknown"] for _i in range(WIDTH - 2)] for _j in range(HEIGHT - 2)]
        }
        self.write_knowledge_base()

    def update(self, visible_world, position, can_shoot, holding_flag):
        # Update knowledge base based on visible_world and other parameters
        position = (position[1] - 1, position[0] - 1)
        self.update_world_knowledge(visible_world, position)

        self.update_enemy_agent_positions(visible_world, position)
        self.update_enemy_flag_position(visible_world, position)
        self.update_my_flag_position(visible_world, position)
        
        self.write_knowledge_base()
        action, direction = self.make_decision(can_shoot, holding_flag, position, visible_world)
        print("update: ", action, direction)
        
        return action, direction
    
    def make_decision(self, can_shoot, holding_flag, current_position, visible_world):
        print("Knowledge Base:", self.knowledge_base)

        if not any(self.knowledge_base.values()):
            action = "move"
            direction = random.choice(["up", "down", "left", "right"])
        else:
            enemy_flag_position = self.knowledge_base["enemy_flag_position"]
            print("Enemy Flag Positions:", enemy_flag_position)

            if enemy_flag_position:
                target_position = enemy_flag_position[0]
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
                # Handle case when enemy_flag_position is empty
                action = "move"
                direction = random.choice(["up", "down", "left", "right"])

        print("Decision:", action, direction)
        return action, direction


    def determine_direction_towards_enemy(self, current_position, visible_world):
        if self.knowledge_base["enemy_agent_positions"] is not []:
            enemy_position = self.knowledge_base["enemy_agent_positions"]
            target_position = self.knowledge_base["my_flag_position"] if enemy_position in self.knowledge_base["enemy_flag_position"] else enemy_position
            _, shortest_path = self.astar(current_position, target_position, visible_world)
            direction = self.get_direction(current_position, shortest_path)
            return direction

    def determine_direction_towards_flag(self, holding_flag, current_position, visible_world):
        target_position = self.knowledge_base["my_flag_position"] if not holding_flag else random.choice(self.knowledge_base["enemy_flag_position"])
        _, shortest_path = self.astar(current_position, target_position, visible_world)
        direction = self.get_direction(current_position, shortest_path)
        return direction

    def astar(self, agent_pos, target_pos, visible_world):
        def is_valid(position):
            x, y = position
            return 0 <= x < HEIGHT - 2 and 0 <= y < WIDTH - 2
        
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
            elif visible_world[x][y] == ASCII_TILES[MY + "_flag"]:
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
    
    def update_enemy_agent_positions(self, visible_world, position):
        memory_enemies = self.get_positions_from_world_knowledge(ASCII_TILES[ENEMY + "_agent"]) + \
            self.get_positions_from_world_knowledge(ASCII_TILES[ENEMY + "_agent_f"])

        if memory_enemies:
            if len(memory_enemies) > 3:
                visible_enemies = self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[ENEMY + "_agent"]) + \
                    self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[ENEMY + "_agent_f"])

                self.knowledge_base["enemy_agent_positions"] = visible_enemies
                self.remove_incorrect_positions(memory_enemies, visible_enemies)
            else:
                self.knowledge_base["enemy_agent_positions"] = memory_enemies

    def update_enemy_flag_position(self, visible_world, position):
        memory_flags = self.get_positions_from_world_knowledge(ASCII_TILES[ENEMY + "_flag"]) + \
            self.get_positions_from_world_knowledge(ASCII_TILES[MY + "_agent_f"])
        
        visible_flags = self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[ENEMY + "_flag"]) + \
            self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[MY + "_agent_f"])

        if visible_flags:
            self.knowledge_base["enemy_flag_position"] = visible_flags
            if visible_flags != memory_flags:
                self.remove_incorrect_positions(memory_flags, visible_flags)
        elif memory_flags:
            self.knowledge_base["enemy_flag_position"] = memory_flags

    def update_my_flag_position(self, visible_world, position):
        memory_flags = self.get_positions_from_world_knowledge(ASCII_TILES[MY + "_flag"]) + \
            self.get_positions_from_world_knowledge(ASCII_TILES[ENEMY + "_agent_f"])
        
        visible_flags = self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[MY + "_flag"]) + \
            self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[ENEMY + "_agent_f"])

        if visible_flags:
            self.knowledge_base["my_flag_position"] = visible_flags
            if visible_flags != memory_flags:
                self.remove_incorrect_positions(memory_flags, visible_flags)
        elif memory_flags:
            self.knowledge_base["my_flag_position"] = memory_flags

    def update_world_knowledge(self, visible_world, position):
        # read latest knowledge base for max information
        with open(MEMORY_FILE, "r") as openfile:
            knowledge_base = json.load(openfile)
        self.knowledge_base["world_knowledge"] = knowledge_base["world_knowledge"]

        for i in range(len(visible_world)):
            for j in range(len(visible_world[0])):
                x = i - 4 + position[1]
                y = j - 4 + position[0]
                if (visible_world[j][i] != ASCII_TILES["unknown"]
                    and x in range(len(self.knowledge_base["world_knowledge"][0]))
                    and y in range(len(self.knowledge_base["world_knowledge"]))):
                    self.knowledge_base["world_knowledge"][y][x] = visible_world[j][i]
                    
    def write_knowledge_base(self):
        # Serializing json
        json_base = json.dumps(self.knowledge_base)
        
        # Writing knowledge so each agent can know what its teammates have learned
        with open(MEMORY_FILE, "w") as outfile:
            outfile.write(json_base)

    def get_positions_from_visible_world(self, visible_world, position, ascii_char):
        positions = []
        rows = [''.join(row) for row in visible_world]
        for row_idx, row in enumerate(rows):
            for col_idx, char in enumerate(row):
                if char == ascii_char:
                    positions.append((row_idx - 4 + position[0], col_idx - 4 + position[1]))

        return positions
    
    def get_positions_from_world_knowledge(self, ascii_char):
        positions = []
        rows = [''.join(row) for row in self.knowledge_base["world_knowledge"]]
        for row_idx, row in enumerate(rows):
            for col_idx, char in enumerate(row):
                if char == ascii_char:
                    positions.append((row_idx, col_idx))

        return positions
    
    def remove_incorrect_positions(self, list_1, list_2):
        for pos in list(set(list_1).difference(list_2)):
                    self.knowledge_base["world_knowledge"][pos[0]][pos[1]] = ASCII_TILES["empty"]

    def terminate(self, reason):
        if reason == "died":
            print(self.color, self.index, "died")
