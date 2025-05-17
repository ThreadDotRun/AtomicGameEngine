import pygame

class ResourceType:
    TYPES = {
        "wheat": {"color": (255, 215, 0)},
        "iron": {"color": (169, 169, 169)}
    }

    @staticmethod
    def init_sprites():
        for resource, data in ResourceType.TYPES.items():
            surface = pygame.Surface((20, 20), pygame.SRCALPHA)
            if resource == "wheat":
                pygame.draw.line(surface, data["color"], (10, 0), (10, 20), 3)
                pygame.draw.line(surface, data["color"], (5, 5), (15, 15), 2)
            elif resource == "iron":
                pygame.draw.rect(surface, data["color"], (5, 5, 10, 10))
            data["sprite"] = surface