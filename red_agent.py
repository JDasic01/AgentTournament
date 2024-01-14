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

WALL_COST = 10000  
CAPTURE_FLAG_COST = 0
EMPTY_STEP_COST = 1
FEAR_OF_UNKNOWN = 1 
UNKNOWN_STEP_COST = EMPTY_STEP_COST * FEAR_OF_UNKNOWN
FEAR_OF_ENEMY = 8 
SHOOTING_COST = 8

ENEMY = "blue"
MY = "red"
MEMORY_FILE = MY + "_knowledge_base.json"

class Agent:
    
    def __init__(self, color, index):
        self.color = color
        self.index = index
        self.positon = None
        self.knowledge_base = {
            "enemy_agent_positions": [],
            "enemy_flag_position": [],
            "my_flag_position": [],
            "guarding_agent_position": None,
            "target_positions": {},
            "world_knowledge": [[ASCII_TILES["unknown"] for _i in range(WIDTH - 2)] for _j in range(HEIGHT - 2)]
        }
        self.write_knowledge_base()

    def update(self, visible_world, position, can_shoot, holding_flag):
        # Update knowledge base based on visible_world and other parameters
        position = (position[1] - 1, position[0] - 1)
        self.position = position
        self.update_world_knowledge(visible_world, position)
        self.update_enemy_agent_positions(visible_world, position)
        self.update_enemy_flag_position(visible_world, position)
        self.update_my_flag_position(visible_world, position)
        self.update_guarding_agent_position(visible_world, position)
        
        # Make a decision based on agent world knowledge
        action, direction = self.make_decision(can_shoot, holding_flag, position, self.knowledge_base["world_knowledge"], visible_world)

        self.write_knowledge_base()
        print(self.knowledge_base["enemy_flag_position"])
        print("index: " + str(self.index) + "   current pos: " + str(position) + "    target pos: " + 
              str(self.knowledge_base["target_positions"].get(str(self.index) + "_pos")) +
              "     move: " + str(action) + "    direciton: " + str(direction))
        return action, direction

    def make_decision(self, can_shoot, holding_flag, current_position, world_knowledge, visible_world):
        def recalculate_target_position(current_position):
            if self.knowledge_base["guarding_agent_position"] and current_position == self.knowledge_base["guarding_agent_position"]:
                target_position = self.knowledge_base["my_flag_position"][0]
                target_sign = ASCII_TILES[MY + "_flag"]
            else:
                if holding_flag:
                    target_position = self.knowledge_base["my_flag_position"][0]
                    target_sign = ASCII_TILES[MY + "_flag"]
                elif len(self.knowledge_base["enemy_flag_position"]) > 0:
                   target_position = self.knowledge_base["enemy_flag_position"][0]
                   target_sign = ASCII_TILES[ENEMY + "_flag"]
                else:
                    unknown = self.get_positions_from_world_knowledge(ASCII_TILES["unknown"])
                    distance = [abs(pos[0]-current_position[0]) + abs(pos[1]-current_position[1]) +
                                abs(pos[0]-self.knowledge_base["my_flag_position"][0][0]) + 
                                abs(pos[1]-self.knowledge_base["my_flag_position"][0][1])
                                for pos in unknown]
                    indices = [i for i, x in enumerate(distance) if x == max(distance)]
                    target_position = unknown[random.choice(indices)]
                    target_sign = ASCII_TILES["unknown"]
            return target_position, target_sign
        
        target_position = self.knowledge_base["target_positions"].get(str(self.index) + "_pos")
        target_sign = self.knowledge_base["target_positions"].get(str(self.index) + "_sign")

        if target_position:
            if [target_position] != self.knowledge_base["enemy_flag_position"] and \
                len(self.knowledge_base["enemy_flag_position"]) > 0:
                target_position, target_sign  = recalculate_target_position(current_position)
                self.knowledge_base["target_positions"][str(self.index) + "_pos"] = target_position
                self.knowledge_base["target_positions"][str(self.index) + "_sign"] = target_sign
            elif self.knowledge_base["world_knowledge"][target_position[0]][target_position[1]] != target_sign:
                target_position, target_sign  = recalculate_target_position(current_position)
                self.knowledge_base["target_positions"][str(self.index) + "_pos"] = target_position
                self.knowledge_base["target_positions"][str(self.index) + "_sign"] = target_sign

            target_position = tuple(target_position)
        else:
            target_position, target_sign = recalculate_target_position(current_position)
            self.knowledge_base["target_positions"][str(self.index) + "_pos"] = target_position
            self.knowledge_base["target_positions"][str(self.index) + "_sign"] = target_sign
        
        shortest_path = self.astar(current_position, target_position, world_knowledge)
        if len(shortest_path) > 0:
            action, direction = self.get_action_and_direction(current_position, shortest_path, can_shoot, visible_world)
        return action, direction

    def astar(self, agent_pos, target_pos, world_knowledge):
        def is_valid(position):
            x, y = position
            return 0 <= x < HEIGHT - 2 and 0 <= y < WIDTH - 2
        
        def generate_neighbors(pos):
            row, col = pos
            neighbors = [(row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)]
            return [neighbor for neighbor in neighbors if is_valid(neighbor)]
        
        def return_path(came_from, start, goal):
            path = []
            current = goal
            while current != start:
                if current not in came_from:
                    return None  # Goal is not reachable
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]

        def heuristic(a, b):
            return math.sqrt((b[0] - a[0])**2 + (b[1] - a[1])**2)

        def cost_from_const(pos, world_knowledge):
            x, y = pos
            if world_knowledge[x][y] == ASCII_TILES["empty"]:
                return EMPTY_STEP_COST  
            elif world_knowledge[x][y] == ASCII_TILES["wall"]:
                return WALL_COST
            elif world_knowledge[x][y] == ASCII_TILES["bullet"]:
                return WALL_COST
            elif world_knowledge[x][y] == ASCII_TILES["unknown"]:
                return UNKNOWN_STEP_COST 
            elif world_knowledge[x][y] == ASCII_TILES[ENEMY + "_agent"] or world_knowledge[x][y] == ASCII_TILES[ENEMY + "_agent_f"]:
                return FEAR_OF_ENEMY
            elif world_knowledge[x][y] == ASCII_TILES[MY + "_agent"] or world_knowledge[x][y] == ASCII_TILES[MY + "_agent_f"]:
                return EMPTY_STEP_COST ## WALL_COST
            elif world_knowledge[x][y] == ASCII_TILES[ENEMY + "_flag"] :
                return CAPTURE_FLAG_COST
            elif world_knowledge[x][y] == ASCII_TILES[MY + "_flag"] :
                return WALL_COST

        start = agent_pos
        goal = target_pos
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {start: None}
        g_cost = {start: 0}

        while open_set:
            _, current_pos = heapq.heappop(open_set)

            if current_pos == goal:
                return return_path(came_from, start, goal)

            neighbors = generate_neighbors(current_pos)
            for neighbor in neighbors:
                cost = cost_from_const(neighbor, world_knowledge)
                tentative_g_cost = g_cost[current_pos] + cost
                if neighbor in g_cost and tentative_g_cost >= g_cost[neighbor]:
                    continue
                g_cost[neighbor] = tentative_g_cost
                total_cost = tentative_g_cost + heuristic(neighbor, goal)
                heapq.heappush(open_set, (total_cost, neighbor))
                came_from[neighbor] = current_pos
        path = return_path(came_from, start, goal)
        if path:
            return path
        else: 
            return []

    def get_action_and_direction(self, current_pos, shortest_path, can_shoot, visible_world):
        def direction_towards_enemy(current_pos):
            directions = {"row": [], "col": []}
            for pos in self.knowledge_base["enemy_agent_positions"]:
                if pos[0] == current_pos[0]:
                    directions["row"].append("right" if pos[1] > current_pos[1] else "left")
                elif pos[1] == current_pos[1]:
                    directions["col"].append("down" if pos[0] > current_pos[0] else "up")
            return directions

        def move_towards_position(current_pos, next_pos):
            if next_pos[0] < current_pos[0]:
                return 'move', 'up'
            elif next_pos[0] > current_pos[0]:
                return 'move', 'down'
            elif next_pos[1] < current_pos[1]:
                return 'move', 'left'
            elif next_pos[1] > current_pos[1]:
                return 'move', 'right'

        def shoot_towards_direction(directions):
            if len(directions["col"]) == 0:
                return 'shoot', directions["row"][0] if len(directions["row"]) > 0 else None
            elif len(directions["row"]) == 0:
                return 'shoot', directions["col"][0] if len(directions["col"]) > 0 else None
            else:
                return 'shoot', directions["row"][0]

        directions = direction_towards_enemy(current_pos)
        in_row_col, _ = self.enemy_in_row_or_col(current_pos, visible_world)

        if len(shortest_path) > 1:
            next_pos = shortest_path[1]

            if (len(directions["row"]) > 0 or len(directions["col"]) > 0) and can_shoot and in_row_col:
                return shoot_towards_direction(directions)
            else:
                return move_towards_position(current_pos, next_pos)
        else:
            return random.choice([('move', 'up'), ('move', 'down'), ('move', 'left'), ('move', 'right')])
    
    def enemy_in_row_or_col(self, current_pos, visible_world):
        def no_walls_between_positions(pos1, pos2, visible_world):
            def is_valid_position(pos):
                return 0 <= pos[0] < len(visible_world) and 0 <= pos[1] < len(visible_world[0])

            if pos1[0] == pos2[0]:
                start_col = min(pos1[1], pos2[1])
                end_col = max(pos1[1], pos2[1])
                return all(is_valid_position((pos1[0], col)) and visible_world[col][pos1[0]] != ASCII_TILES["wall"] for col in range(start_col + 1, end_col))
            elif pos1[1] == pos2[1]:
                start_row = min(pos1[0], pos2[0])
                end_row = max(pos1[0], pos2[0])
                return all(is_valid_position((row, pos1[1])) and visible_world[pos1[1]][row] != ASCII_TILES["wall"] for row in range(start_row + 1, end_row))
            else:
                return False

        for pos in self.knowledge_base["enemy_agent_positions"]:
            if pos[0] == current_pos[0] and no_walls_between_positions(current_pos, pos, visible_world):
                return True, "row"
            elif pos[1] == current_pos[1] and no_walls_between_positions(current_pos, pos, visible_world):
                return True, "col"
        return False, None

    
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
        memory_flags = self.get_positions_from_world_knowledge(ASCII_TILES[ENEMY + "_flag"])
        
        visible_flags = self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[ENEMY + "_flag"])

        if visible_flags:
            self.knowledge_base["enemy_flag_position"] = visible_flags
            if visible_flags != memory_flags:
                self.remove_incorrect_positions(memory_flags, visible_flags)
        elif memory_flags:
            self.knowledge_base["enemy_flag_position"] = memory_flags

    def update_my_flag_position(self, visible_world, position):
        memory_flags = self.get_positions_from_world_knowledge(ASCII_TILES[MY + "_flag"])
        
        visible_flags = self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[MY + "_flag"]) + \
            self.get_positions_from_visible_world(visible_world, position, ASCII_TILES[ENEMY + "_agent_f"])

        if visible_flags:
            self.knowledge_base["my_flag_position"] = visible_flags
            if visible_flags != memory_flags:
                self.remove_incorrect_positions(memory_flags, visible_flags)
        elif memory_flags:
            self.knowledge_base["my_flag_position"] = memory_flags

    def update_guarding_agent_position(self, visible_world, position):
        memory_agents = self.get_positions_from_world_knowledge(ASCII_TILES[MY + "_agent"]) + \
            self.get_positions_from_world_knowledge(ASCII_TILES[MY + "_agent_f"])
        
        print("broj agenata: " + str(len(memory_agents)))
        if len(memory_agents) < 2:
            self.knowledge_base["guarding_agent_position"] = None
            for key, value in self.knowledge_base["target_positions"].items():
                if value in self.knowledge_base["my_flag_position"]:
                    self.knowledge_base[key.replace("pos", "sign")] = ASCII_TILES["empty"]
        elif self.knowledge_base["guarding_agent_position"] is None or not self.knowledge_base["guarding_agent_position"] in memory_agents:
            my_flags = self.get_positions_from_world_knowledge(ASCII_TILES[MY + "_flag"])

            if my_flags and len(memory_agents)>0:
                distance = [abs(pos[0]-my_flags[0][0]) + 
                            abs(pos[1]-my_flags[0][1])
                            for pos in memory_agents]
                closest_agent = distance.index(min(distance))
                self.knowledge_base["guarding_agent_position"] = memory_agents[closest_agent]
            else:
                self.knowledge_base["guarding_agent_position"] = memory_agents[1]

    def update_world_knowledge(self, visible_world, position):
        # read latest knowledge base for max information
        with open(MEMORY_FILE, "r") as openfile:
            knowledge_base = json.load(openfile)
        self.knowledge_base["world_knowledge"] = knowledge_base["world_knowledge"]
        self.knowledge_base["target_positions"] = knowledge_base["target_positions"]

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
            x, y = self.position
            self.knowledge_base["world_knowledge"][x][y] = ASCII_TILES["empty"]
            self.write_knowledge_base()
            print(self.color, self.index, "died")
