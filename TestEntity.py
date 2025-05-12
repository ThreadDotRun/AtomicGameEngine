from typing import Optional
from CoordinateSystem import CoordinateSystem, Coordinate3D
from CoordinateSystemDML import CoordinateSystemDML
from CoordinateSystemPersistence import CoordinateSystemPersistence
from Entity import Entity  # Assuming the Entity class is in a file named Entity.py

# Subclass for a Player entity
class Player(Entity):
    def __init__(self, entity_id: str, position: Coordinate3D, coordinate_system: CoordinateSystem,
                 dml=None, persistence=None):
        super().__init__(entity_id, position, coordinate_system, dml, persistence)
        self.health = 100
    def update(self):
        if self.position:
            new_pos = (self.position[0] + 0.1, self.position[1], self.position[2])
            self.update_position(new_pos)
            if self.is_near_geometry("wall", 0.5):
                print(f"{self.entity_id} is near a wall!")

cs = CoordinateSystem()
persistence = CoordinateSystemPersistence("game_db")
dml = CoordinateSystemDML("game_db")
cs.add_static_polygon("wall1", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], "wall")

player = Player("player_1", (1.0, 0.0, 0.0), cs, dml, persistence)
player.update()  # Updates position, prints if near wall
print(player.position)  # (1.1, 0.0, 0.0)
print(player.get_nearby_entities((0.0, 0.0, 0.0), (2.0, 2.0, 2.0)))  # {"player_1": (1.1, 0.0, 0.0)}
player.save_state()  # Persists state
player.remove()  # Removes entity