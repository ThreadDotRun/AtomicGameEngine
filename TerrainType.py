import pygame
import json
import math
import random
from typing import List, Tuple

class TerrainType:
    # Fallback configuration in case JSON loading fails
    DEFAULT_TYPES = {
        "ocean": {
            "color": [0, 105, 148],
            "weight": 0.3,
            "move_cost": 2,
            "sprite": {
                "background": {"color": [0, 105, 148]},
                "shapes": [
                    {
                        "type": "sine_wave",
                        "color": [0, 50, 100],
                        "count": 4,
                        "amplitude": 0.1,
                        "frequency": 0.2,
                        "thickness": 0.05
                    }
                ]
            }
        },
        "plain": {
            "color": [139, 195, 74],
            "weight": 0.3,
            "move_cost": 1,
            "sprite": {
                "background": {"color": [139, 195, 74]},
                "shapes": [
                    {
                        "type": "grass",
                        "color": [100, 150, 50],
                        "count": 12,
                        "size": 0.05,
                        "spread": 0.9
                    }
                ]
            }
        },
        "hill": {
            "color": [96, 125, 139],
            "weight": 0.2,
            "move_cost": 2,
            "sprite": {
                "background": {"color": [96, 125, 139]},
                "shapes": [
                    {
                        "type": "contour",
                        "color": [70, 100, 110],
                        "count": 3,
                        "size": 0.6,
                        "offset": 0.05
                    }
                ]
            }
        },
        "mountain": {
            "color": [69, 90, 100],
            "weight": 0.1,
            "move_cost": 4,
            "sprite": {
                "background": {"color": [69, 90, 100]},
                "shapes": [
                    {
                        "type": "peak",
                        "color": [50, 70, 80],
                        "base_width": 0.8,
                        "height": 0.75,
                        "snow_color": [200, 200, 200],
                        "snow_height": 0.2
                    }
                ]
            }
        },
        "stream": {
            "color": [73, 196, 218],
            "weight": 0.1,
            "move_cost": 3,
            "sprite": {
                "background": {"color": [73, 196, 218]},
                "shapes": [
                    {
                        "type": "flow",
                        "color": [50, 150, 200],
                        "width": 0.3,
                        "curve": 0.2,
                        "thickness": 0.1
                    }
                ]
            }
        },
        "forest": {
            "color": [34, 139, 34],
            "weight": 0.2,
            "move_cost": 3,
            "sprite": {
                "background": {"color": [34, 139, 34]},
                "shapes": [
                    {
                        "type": "polygon",
                        "color": [0, 100, 0],
                        "count": 8,
                        "size": 0.1,
                        "spread": 0.9,
                        "points": [
                            [0.0, -0.5],
                            [-0.5, 0.5],
                            [0.5, 0.5]
                        ]
                    }
                ]
            }
        },
        "desert": {
            "color": [194, 178, 128],
            "weight": 0.2,
            "move_cost": 2,
            "sprite": {
                "background": {"color": [194, 178, 128]},
                "shapes": [
                    {
                        "type": "sine_wave",
                        "color": [210, 180, 140],
                        "count": 3,
                        "amplitude": 0.05,
                        "frequency": 0.15,
                        "thickness": 0.1
                    }
                ]
            }
        },
        "swamp": {
            "color": [95, 115, 75],
            "weight": 0.1,
            "move_cost": 4,
            "sprite": {
                "background": {"color": [95, 115, 75]},
                "shapes": [
                    {
                        "type": "ellipse",
                        "color": [0, 105, 148, 150],
                        "count": 6,
                        "size": [0.15, 0.1],
                        "spread": 0.8
                    }
                ]
            }
        }
    }

    TYPES = {}

    @staticmethod
    def load_config(config_path: str = "terrain_config.json") -> None:
        """Load terrain configuration from a JSON file."""
        try:
            with open(config_path, 'r') as f:
                TerrainType.TYPES = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading {config_path}: {e}. Using default configuration.")
            TerrainType.TYPES = TerrainType.DEFAULT_TYPES

    @staticmethod
    def init_sprites() -> None:
        """Initialize sprites for each terrain type based on config."""
        for terrain, data in TerrainType.TYPES.items():
            surface = pygame.Surface((40, 40), pygame.SRCALPHA)
            width, height = surface.get_size()

            # Draw background
            bg_color = data["sprite"]["background"]["color"]
            surface.fill(bg_color if len(bg_color) == 3 else bg_color[:3])

            # Draw shapes
            for shape in data["sprite"]["shapes"]:
                color = shape["color"]
                color = tuple(color) if len(color) == 4 else tuple(color) + (255,)

                if shape["type"] == "sine_wave":
                    for i in range(shape["count"]):
                        y_base = i * height / shape["count"]
                        points = []
                        for x in range(0, width + 1, 1):
                            y = y_base + math.sin(x * shape["frequency"]) * shape["amplitude"] * height
                            points.append((x, y))
                        pygame.draw.lines(surface, color, False, points, int(width * shape["thickness"]))

                elif shape["type"] == "circle":
                    center_x, center_y = [c * width for c in shape["center"]]
                    radius = shape["radius"] * width
                    for i in range(shape["count"]):
                        offset = i * shape["spacing"] * width
                        pygame.draw.circle(surface, color, (center_x + offset, center_y), radius)

                elif shape["type"] == "grass":
                    for _ in range(shape["count"]):
                        x = width * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        y = height * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        size = shape["size"] * width
                        points = [(x, y - size), (x - size/2, y + size), (x + size/2, y + size)]
                        pygame.draw.polygon(surface, color, points)

                elif shape["type"] == "flower":
                    for _ in range(shape["count"]):
                        x = width * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        y = height * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        pygame.draw.circle(surface, color, (x, y), shape["size"] * width)

                elif shape["type"] == "contour":
                    base_size = shape["size"] * width
                    for i in range(shape["count"]):
                        size = base_size * (1 - i * shape["offset"])
                        pos = (width - size) / 2, (height - size) / 2
                        pygame.draw.rect(surface, color, (pos[0], pos[1], size, size), 0, border_radius=int(size * 0.2))

                elif shape["type"] == "rock":
                    for _ in range(shape["count"]):
                        x = width * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        y = height * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        size = shape["size"] * width
                        points = [
                            (x + size * random.uniform(-0.5, 0.5), y + size * random.uniform(-0.5, 0.5))
                            for _ in range(4)
                        ]
                        pygame.draw.polygon(surface, color, points)

                elif shape["type"] == "peak":
                    base_width = shape["base_width"] * width
                    peak_height = shape["height"] * height
                    points = [
                        (width * 0.5, height * (1 - shape["height"])),
                        (width * (0.5 - base_width/2), height),
                        (width * (0.5 + base_width/2), height)
                    ]
                    pygame.draw.polygon(surface, color, points)
                    # Snow cap
                    snow_points = [
                        (width * 0.5, height * (1 - shape["height"])),
                        (width * (0.5 - base_width/2 * shape["snow_height"]/shape["height"]), height * (1 - shape["snow_height"])),
                        (width * (0.5 + base_width/2 * shape["snow_height"]/shape["height"]), height * (1 - shape["snow_height"]))
                    ]
                    pygame.draw.polygon(surface, shape["snow_color"], snow_points)

                elif shape["type"] == "ridge":
                    for i in range(shape["count"]):
                        offset = i * shape["offset"] * width
                        points = [
                            (width * (0.5 + offset), height * 0.5),
                            (width * (0.5 + offset - shape["width"]/2), height),
                            (width * (0.5 + offset + shape["width"]/2), height)
                        ]
                        pygame.draw.polygon(surface, color, points)

                elif shape["type"] == "flow":
                    points = [
                        (width * 0.25, 0),
                        (width * (0.25 + shape["curve"]), height * 0.5),
                        (width * 0.75, height)
                    ]
                    pygame.draw.lines(surface, color, False, points, int(width * shape["width"]))
                    pygame.draw.lines(surface, color, False, points, int(width * shape["thickness"]))

                elif shape["type"] == "ripple":
                    for _ in range(shape["count"]):
                        x = width * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        y = height * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        pygame.draw.ellipse(surface, color, (x - shape["size"] * width, y - shape["size"] * width / 2, shape["size"] * width * 2, shape["size"] * width))

                elif shape["type"] == "polygon":
                    for _ in range(shape["count"]):
                        x = width * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        y = height * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        size = shape["size"] * width
                        points = [(x + size * px, y + size * py) for px, py in shape["points"]]
                        pygame.draw.polygon(surface, color, points)

                elif shape["type"] == "rect":
                    for _ in range(shape["count"]):
                        x = width * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        y = height * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        w, h = [s * width for s in shape["size"]]
                        pygame.draw.rect(surface, color, (x - w/2, y - h/2, w, h))

                elif shape["type"] == "line":
                    for _ in range(shape["count"]):
                        x = width * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        y = height * (0.5 + random.uniform(-shape["spread"]/2, shape["spread"]/2))
                        start = [x + width * shape["start"][0], y + height * shape["start"][1]]
                        end = [x + width * shape["end"][0], y + height * shape["end"][1]]
                        pygame.draw.line(surface, color, start, end, int(width * shape["thickness"]))

            data["sprite"] = surface