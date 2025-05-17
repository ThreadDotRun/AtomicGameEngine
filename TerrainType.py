import pygame

class TerrainType:
    TYPES = {
        "ocean": {"color": (0, 105, 148), "weight": 0.3, "move_cost": 2},
        "plain": {"color": (139, 195, 74), "weight": 0.3, "move_cost": 1},
        "hill": {"color": (96, 125, 139), "weight": 0.2, "move_cost": 2},
        "mountain": {"color": (69, 90, 100), "weight": 0.1, "move_cost": 4},
        "stream": {"color": (73, 196, 218), "weight": 0.1, "move_cost": 3}
    }

    @staticmethod
    def init_sprites():
        for terrain, data in TerrainType.TYPES.items():
            surface = pygame.Surface((40, 40), pygame.SRCALPHA)
            surface.fill(data["color"])
            width, height = surface.get_size()
            # Scale drawing elements relative to sprite size
            if terrain == "ocean":
                for i in range(5):
                    y = i * height / 5
                    pygame.draw.line(surface, (0, 50, 100), (0, y), (width, y), int(width / 20))
            elif terrain == "plain":
                for i in range(8):
                    x = i * width / 8
                    y = i * height / 8
                    pygame.draw.circle(surface, (100, 150, 50), (int(x), int(y)), int(width / 20))
            elif terrain == "hill":
                rect_size = width * 0.5  # 50% of sprite width
                rect_pos = (width * 0.25, height * 0.25)  # Center the rectangle
                pygame.draw.rect(surface, (70, 100, 110), (rect_pos[0], rect_pos[1], rect_size, rect_size))
            elif terrain == "mountain":
                points = [(width * 0.5, height * 0.125),  # Top
                          (width * 0.25, height * 0.875),  # Bottom left
                          (width * 0.75, height * 0.875)]  # Bottom right
                pygame.draw.polygon(surface, (50, 70, 80), points)
            elif terrain == "stream":
                pygame.draw.line(surface, (50, 150, 200), (width * 0.25, 0), (width * 0.75, height), int(width / 10))
            data["sprite"] = surface