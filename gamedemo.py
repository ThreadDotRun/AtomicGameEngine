import asyncio
import platform
import pygame
import math
from CoordinateSystem import CoordinateSystem, Coordinate3D
from CoordinateSystemPersistence import CoordinateSystemPersistence
from CoordinateSystemDML import CoordinateSystemDML
from Config import Config
from TerrainType import TerrainType
from ResourceType import ResourceType
from Unit import Unit
from City import City
from Pathfinding import Pathfinding
from HexUtils import HexUtils
from HexMap import HexMap

class Game:
    def __init__(self):
        pygame.init()
        Config.WIDTH = 1900  # Fixed for Studio
        Config.HEIGHT = 800
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption("Hex Civ Map")
        self.clock = pygame.time.Clock()
        TerrainType.load_config()  # Load terrain config from JSON
        TerrainType.init_sprites()
        ResourceType.init_sprites()
        self.cs = CoordinateSystem()
        self.persistence = CoordinateSystemPersistence("game_map")
        self.map = HexMap(Config.GRID_WIDTH, Config.GRID_HEIGHT, self.cs, self.persistence)
        self.dml = CoordinateSystemDML(self.persistence.conn)
        # Initialize multiple units at different hex coordinates
        self.units = [
            Unit("unit_0", HexUtils.hex_to_cartesian(0, 0, Config.HEX_SIZE), self.cs),
            Unit("unit_1", HexUtils.hex_to_cartesian(1, 1, Config.HEX_SIZE), self.cs),
            Unit("unit_2", HexUtils.hex_to_cartesian(-1, -1, Config.HEX_SIZE), self.cs)
        ]
        self.cities = [City("city_0", HexUtils.hex_to_cartesian(2, 2, Config.HEX_SIZE), self.cs, "Capital")]
        self.persistence.save_coordinate_system(self.cs)
        self.camera_offset = [0, 0]
        self.dragging = False
        self.last_pos = (0, 0)
        self.selected_unit = None
        self.hover_hex = None
        self.path = []
        self.turn = 1
        self.font = pygame.font.Font(None, int(14 * Config.WIDTH / 800))

    def end_turn(self):
        self.turn += 1
        for unit in self.units:
            unit.movement_points = Config.UNIT_MOVEMENT_POINTS
        self.selected_unit = None
        self.path = []

    async def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.persistence.save_coordinate_system(self.cs)
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mx, my = pygame.mouse.get_pos()
                        q, r = HexUtils.pixel_to_hex(mx, my, Config.HEX_SIZE, self.camera_offset)
                        pos = HexUtils.hex_to_cartesian(q, r, Config.HEX_SIZE)
                        # Use max_distance to limit unit selection to nearby units
                        nearest = self.dml.find_nearest_entity(pos, "unit_", max_distance=Config.HEX_SIZE)
                        if nearest:
                            unit_id, _ = nearest
                            self.selected_unit = next((u for u in self.units if u.entity_id == unit_id), None)
                            print(f"Selected unit: {self.selected_unit.entity_id if self.selected_unit else None}")
                            self.path = []
                        else:
                            if self.selected_unit and self.selected_unit.movement_points > 0:
                                start = self.cs.get_entity_position(self.selected_unit.entity_id)
                                path = Pathfinding.a_star(start, pos, self.cs, self.dml)
                                print(f"Path found: {path}")
                                if path:
                                    total_cost = 0
                                    for i in range(1, len(path)):
                                        q, r = HexUtils.cartesian_to_hex(path[i][0], path[i][1], Config.HEX_SIZE)
                                        terrain = self.cs.get_static_geometry(f"hex_{q}_{r}")
                                        print(f"Hex {q},{r}: {terrain}")
                                        if terrain:
                                            total_cost += TerrainType.TYPES[terrain["category"]]["move_cost"]
                                        else:
                                            total_cost += 1  # Default cost for missing terrain
                                    print(f"Total movement cost: {total_cost}, Movement points: {self.selected_unit.movement_points}")
                                    if total_cost <= self.selected_unit.movement_points:
                                        self.cs.update_entity_position(self.selected_unit.entity_id, pos)
                                        self.selected_unit.movement_points -= total_cost
                                        self.path = []
                                    else:
                                        self.path = path
                        self.dragging = True
                        self.last_pos = event.pos
                    elif event.button == 3:
                        self.persistence.save_coordinate_system(self.cs)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False
                elif event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    q, r = HexUtils.pixel_to_hex(mx, my, Config.HEX_SIZE, self.camera_offset)
                    self.hover_hex = (q, r) if self.cs.get_static_geometry(f"hex_{q}_{r}") else None
                    if self.dragging:
                        dx, dy = mx - self.last_pos[0], my - self.last_pos[1]
                        self.camera_offset[0] -= dx
                        self.camera_offset[1] -= dy
                        self.last_pos = event.pos
                elif event.type == pygame.MOUSEWHEEL:
                    Config.HEX_SIZE = max(Config.MIN_HEX_SIZE,
                                        min(Config.MAX_HEX_SIZE,
                                            Config.HEX_SIZE + event.y * 5))
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.end_turn()
                    elif event.key == pygame.K_ESCAPE:
                        self.persistence.save_coordinate_system(self.cs)
                        return

            self.screen.fill((0, 0, 0))

            # Render all hexes in priority order (low to high)
            for terrain_type in ["plain", "desert", "forest", "hill", "mountain", "stream", "swamp", "ocean"]:
                for gid, gdata in self.cs.list_static_geometry_by_category(terrain_type).items():
                    q, r = map(int, gid.split("_")[1:])
                    pos = HexUtils.hex_to_cartesian(q, r, Config.HEX_SIZE)
                    HexUtils.draw_hex(self.screen, pos, Config.HEX_SIZE, terrain_type, self.camera_offset)

            for rid, pos in self.cs.get_all_entity_positions().items():
                if rid.startswith("resource_"):
                    resource_type = self.map.resources.get(rid)
                    if resource_type:
                        HexUtils.draw_resource(self.screen, pos, Config.HEX_SIZE, resource_type, self.camera_offset)

            # Visual debugging: Show clicked hex
            if self.hover_hex:
                q, r = self.hover_hex
                pos = HexUtils.hex_to_cartesian(q, r, Config.HEX_SIZE)
                x, y = HexUtils.hex_to_pixel(pos, self.camera_offset)
                pygame.draw.circle(self.screen, (255, 0, 0), (int(x), int(y)), 5)  # Red dot at clicked hex center
                points = [(x + Config.HEX_SIZE * math.cos(math.pi / 3 * i),
                         y + Config.HEX_SIZE * math.sin(math.pi / 3 * i)) for i in range(6)]
                pygame.draw.polygon(self.screen, (255, 255, 0), points, 2)
                terrain = self.cs.get_static_geometry(f"hex_{q}_{r}")["category"]
                label = self.font.render(terrain, True, (0, 0, 0))
                self.screen.blit(label, (x - label.get_width() // 2, y - label.get_height() // 2))

            for city in self.cities:
                pos = self.cs.get_entity_position(city.entity_id)
                if pos:
                    HexUtils.draw_city(self.screen, pos, Config.HEX_SIZE, city, self.camera_offset)

            for unit in self.units:
                pos = self.cs.get_entity_position(unit.entity_id)
                if pos:
                    HexUtils.draw_unit(self.screen, pos, Config.HEX_SIZE, unit, self.camera_offset)
                    if unit == self.selected_unit:
                        x, y = HexUtils.hex_to_pixel(pos, self.camera_offset)
                        pygame.draw.circle(self.screen, (0, 255, 0), (int(x), int(y)), int(Config.HEX_SIZE / 2), 2)
                    label = self.font.render(f"MP: {unit.movement_points}", True, (0, 0, 0))
                    x, y = HexUtils.hex_to_pixel(pos, self.camera_offset)
                    self.screen.blit(label, (x - label.get_width() // 2, y + Config.HEX_SIZE))

            for pos in self.path:
                x, y = HexUtils.hex_to_pixel(pos, self.camera_offset)
                pygame.draw.circle(self.screen, (0, 0, 255), (int(x), int(y)), int(5 * Config.WIDTH / 800))

            turn_label = self.font.render(f"Turn: {self.turn}", True, (0, 0, 0))
            self.screen.blit(turn_label, (10, 10))

            pygame.display.flip()
            self.clock.tick(Config.FPS)
            await asyncio.sleep(1.0 / Config.FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(Game().run())
else:
    if __name__ == "__main__":
        asyncio.run(Game().run())