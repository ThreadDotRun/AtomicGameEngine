import pygame
from CoordinateSystem import Coordinate3D, CoordinateSystem
from Config import Config

class Unit:
    def __init__(self, entity_id: str, position: Coordinate3D, cs: CoordinateSystem, name="Soldier"):
        self.entity_id = entity_id
        self.name = name
        self.movement_points = Config.UNIT_MOVEMENT_POINTS
        cs.add_entity(entity_id, position)
        surface = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 0, 0), (10, 10), 8)
        self.sprite = surface