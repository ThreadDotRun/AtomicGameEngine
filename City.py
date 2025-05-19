import pygame
from CoordinateSystem import Coordinate3D, CoordinateSystem
from Config import Config
from Entity import Entity

class City(Entity):
    def __init__(self, entity_id: str, position: Coordinate3D, cs: CoordinateSystem,
                 dml=None, persistence=None, name: str = "City"):
        super().__init__(entity_id, position, cs, dml, persistence)
        self.name = name
        surface = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.rect(surface, (200, 200, 200), (5, 5, 20, 20))
        pygame.draw.rect(surface, (0, 0, 0), (5, 5, 20, 20), 2)
        self.sprite = surface

    def update(self) -> None:
        """Update city state, e.g., process status effects."""
        if self._persistence:
            from CombatSystem import CombatSystem  # Avoid circular import
            combat_system = CombatSystem(self._coordinate_system, self._dml, self._persistence)
            combat_system.update_status_effects(self.entity_id)