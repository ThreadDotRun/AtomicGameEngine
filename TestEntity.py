from typing import Optional
from CoordinateSystem import CoordinateSystem, Coordinate3D
from CoordinateSystemDML import CoordinateSystemDML
from CoordinateSystemPersistence import CoordinateSystemPersistence
from Entity import Entity  # Assuming the Entity class is in a file named Entity.py

# Example subclass for a Player entity
class Player(Entity):
    def __init__(self, entity_id: str, position: Coordinate3D, coordinate_system: CoordinateSystem,
                 dml: Optional[CoordinateSystemDML] = None, persistence: Optional[CoordinateSystemPersistence] = None):
        super().__init__(entity_id, position, coordinate_system, dml, persistence)
        self.health = 100

    def update(self) -> None:
        # Example: Move player slightly and check proximity to walls
        if self.position:
            new_pos = (self.position[0] + 0.1, self.position[1], self.position[2])
            self.update_position(new_pos)
            if self.is_near_geometry("wall", 0.5):
                print(f"{self.entity_id} is near a wall!")

# Initialize system components
cs = CoordinateSystem()
persistence = CoordinateSystemPersistence("game_db")
dml = CoordinateSystemDML("game_db")

# Add some static geometry
cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "ground_plane")
cs.add_static_polygon("wall1", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], "wall")

# Create a player
player = Player("player_1", (1.0, 0.0, 0.0), cs, dml, persistence)

# Update player state
player.update()

# Query nearby entities
nearby = player.get_nearby_entities((0.0, 0.0, 0.0), (2.0, 2.0, 2.0))
print(f"Nearby entities: {nearby}")

# Save the state
player.save_state()

# Remove the player
player.remove()