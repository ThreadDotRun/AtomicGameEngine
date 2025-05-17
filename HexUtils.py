import math
import pygame
from typing import Tuple, List
from CoordinateSystem import Coordinate3D
from Config import Config
from TerrainType import TerrainType
from ResourceType import ResourceType
from Unit import Unit
from City import City

class HexUtils:
    @staticmethod
    def hex_to_cartesian(q: int, r: int, size: float) -> Coordinate3D:
        x = size * 3 / 2 * q
        y = size * math.sqrt(3) * (r + q / 2)
        return (x, y, 0)

    @staticmethod
    def cartesian_to_hex(x: float, y: float, size: float) -> Tuple[int, int]:
        q = x / (size * 3 / 2)
        r = (y - q * size * math.sqrt(3) / 2) / (size * math.sqrt(3))
        x, z = q, -q - r
        y = -x - z
        rx, ry, rz = round(x), round(y), round(z)
        x_diff, y_diff, z_diff = abs(rx - x), abs(ry - y), abs(rz - z)
        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry - rz
        elif y_diff > z_diff:
            ry = -rx - rz
        return rx, ry

    @staticmethod
    def hex_to_pixel(pos: Coordinate3D, offset: List[float]) -> Tuple[float, float]:
        return (pos[0] - offset[0] + Config.WIDTH / 2,
                pos[1] - offset[1] + Config.HEIGHT / 2)

    @staticmethod
    def pixel_to_hex(x: float, y: float, size: float, offset: List[float]) -> Tuple[int, int]:
        x = (x - Config.WIDTH / 2 + offset[0]) / (size * 3 / 2)
        r = (y - Config.HEIGHT / 2 + offset[1] - x * size * math.sqrt(3) / 2) / (size * math.sqrt(3))
        q = x
        x, z = q, -q - r
        y = -x - z
        rx, ry, rz = round(x), round(y), round(z)
        x_diff, y_diff, z_diff = abs(rx - x), abs(ry - y), abs(rz - z)
        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry - rz
        elif y_diff > z_diff:
            ry = -rx - rz
        return rx, ry

    @staticmethod
    def get_hex_vertices(q: int, r: int, size: float) -> List[Coordinate3D]:
        center = HexUtils.hex_to_cartesian(q, r, size)
        return [(center[0] + size * math.cos(math.pi / 3 * i),
                 center[1] + size * math.sin(math.pi / 3 * i), 0) for i in range(6)]

    @staticmethod
    def draw_hex(surface, pos: Coordinate3D, size: float, terrain: str, offset: List[float]):
        # Calculate the screen position of the hex
        x, y = HexUtils.hex_to_pixel(pos, offset)
        
        # Calculate the vertices of the hex in screen coordinates
        points = [(x + size * math.cos(math.pi / 3 * i), y + size * math.sin(math.pi / 3 * i)) for i in range(6)]
        
        # Get the terrain sprite
        sprite = TerrainType.TYPES[terrain]["sprite"]
        
        # Scale sprite to fit hex (diameter of hex is 2 * size)
        hex_diameter = 2 * size
        scale_factor = hex_diameter / sprite.get_width()  # Original sprite is 40x40
        scaled_sprite = pygame.transform.scale(sprite, (int(sprite.get_width() * scale_factor), int(sprite.get_height() * scale_factor)))
        
        # Calculate the bounding box of the hex to determine the size of the mask surface
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        mask_width = int(max_x - min_x)
        mask_height = int(max_y - min_y)
        
        # Create a mask surface with the same size as the bounding box
        mask_surface = pygame.Surface((mask_width, mask_height), pygame.SRCALPHA)
        
        # Adjust the hex points to be relative to the mask surface (translate to origin)
        adjusted_points = [(p[0] - min_x, p[1] - min_y) for p in points]
        
        # Draw the hexagon on the mask surface (filled white shape on transparent background)
        pygame.draw.polygon(mask_surface, (255, 255, 255), adjusted_points)
        
        # Create a new surface for the masked sprite
        masked_sprite = pygame.Surface((mask_width, mask_height), pygame.SRCALPHA)
        
        # Blit the scaled sprite onto the masked sprite surface at the correct offset
        sprite_x_offset = (mask_width - scaled_sprite.get_width()) // 2
        sprite_y_offset = (mask_height - scaled_sprite.get_height()) // 2
        masked_sprite.blit(scaled_sprite, (sprite_x_offset, sprite_y_offset))
        
        # Apply the mask by setting the alpha channel
        # Convert the mask surface to an alpha mask (0 or 255)
        mask_array = pygame.surfarray.pixels_alpha(mask_surface)
        sprite_array = pygame.surfarray.pixels_alpha(masked_sprite)
        # Multiply the sprite's alpha by the mask's alpha (0 where mask is transparent, unchanged where mask is opaque)
        sprite_array[...] = (sprite_array * (mask_array // 255)).astype(sprite_array.dtype)
        del mask_array, sprite_array  # Unlock the surfaces
        
        # Calculate the position to blit the masked sprite (top-left of the mask surface)
        blit_x = min_x
        blit_y = min_y
        
        # Blit the masked sprite onto the main surface
        surface.blit(masked_sprite, (blit_x, blit_y))
        
        # Draw the hex outline (optional, for visibility)
        pygame.draw.polygon(surface, (50, 50, 50), points, 1)

    @staticmethod
    def draw_unit(surface, pos: Coordinate3D, size: float, unit: Unit, offset: List[float]):
        x, y = HexUtils.hex_to_pixel(pos, offset)
        scale_factor = size / Config.HEX_SIZE
        scaled_sprite = pygame.transform.scale(unit.sprite, (int(20 * scale_factor * 1.2), int(20 * scale_factor * 1.2)))
        sprite_x = x - scaled_sprite.get_width() / 2
        sprite_y = y - scaled_sprite.get_height() / 2
        surface.blit(scaled_sprite, (sprite_x, sprite_y))

    @staticmethod
    def draw_city(surface, pos: Coordinate3D, size: float, city: City, offset: List[float]):
        x, y = HexUtils.hex_to_pixel(pos, offset)
        scale_factor = size / Config.HEX_SIZE
        scaled_sprite = pygame.transform.scale(city.sprite, (int(30 * scale_factor * 1.5), int(30 * scale_factor * 1.5)))
        sprite_x = x - scaled_sprite.get_width() / 2
        sprite_y = y - scaled_sprite.get_height() / 2
        surface.blit(scaled_sprite, (sprite_x, sprite_y))

    @staticmethod
    def draw_resource(surface, pos: Coordinate3D, size: float, resource: str, offset: List[float]):
        x, y = HexUtils.hex_to_pixel(pos, offset)
        scale_factor = size / Config.HEX_SIZE
        sprite = ResourceType.TYPES[resource]["sprite"]
        scaled_sprite = pygame.transform.scale(sprite, (int(20 * scale_factor * 0.5), int(20 * scale_factor * 0.5)))
        sprite_x = x - scaled_sprite.get_width() / 2
        sprite_y = y - scaled_sprite.get_height() / 2
        surface.blit(scaled_sprite, (sprite_x, sprite_y))