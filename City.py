import pygame
from CoordinateSystem import Coordinate3D, CoordinateSystem

class City:
    def __init__(self, entity_id: str, position: Coordinate3D, cs: CoordinateSystem, name="City"):
        self.entity_id = entity_id
        self.name = name
        cs.add_entity(entity_id, position)
        surface = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.rect(surface, (200, 200, 200), (5, 5, 20, 20))
        pygame.draw.rect(surface, (0, 0, 0), (5, 5, 20, 20), 2)
        self.sprite = surface