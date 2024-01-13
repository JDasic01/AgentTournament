TODO:

ispravit funkcije, 
no_enemy_in_row_or_col - true ili false ovisno o tome ako je enemy u row ili col od pozicije trenutnog agenta
directions towards enemy treba vracat up, down, left, right ovisno o tome gdje je enemy agent od pozicije trenutnog agenta 
```
        def no_enemy_in_row_or_col():
        # Implement the logic to check if there is no enemy in the same row or column
            return not (self.knowledge_base["enemy_agent_positions"] and any(
                pos[0] == self.knowledge_base["guarding_agent_position"][0][0] or  # Same row
                pos[1] == self.knowledge_base["guarding_agent_position"][0][1]     # Same column
                for pos in self.knowledge_base["enemy_agent_positions"]
            ))
        
        def direction_towards_enemy():
            # Implement the logic to check if there is no enemy in the same row or column
            return "up"
```
