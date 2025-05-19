import pygame
from CoordinateSystem import Coordinate3D, CoordinateSystem
from Config import Config
from Entity import Entity

class Unit(Entity):
    def __init__(self, entity_id: str, position: Coordinate3D, cs: CoordinateSystem,
                 dml=None, persistence=None, name: str = "Soldier"):
        super().__init__(entity_id, position, cs, dml, persistence)
        self.name = name
        self.movement_points = Config.UNIT_MOVEMENT_POINTS
        surface = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 0, 0), (10, 10), 8)
        self.sprite = surface

    def update(self) -> None:
        """Update unit state, e.g., process status effects."""
        if self._persistence:
            from CombatSystem import CombatSystem  # Avoid circular import
            combat_system = CombatSystem(self._coordinate_system, self._dml, self._persistence)
            combat_system.update_status_effects(self.entity_id)