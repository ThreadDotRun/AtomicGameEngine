import random
from CoordinateSystem import CoordinateSystem, Coordinate3D
from CoordinateSystemPersistence import CoordinateSystemPersistence
from Config import Config
from HexUtils import HexUtils
from TerrainType import TerrainType
from ResourceType import ResourceType
from typing import List, Tuple

class HexMap:
    TERRAIN_RULES = {
        "ocean": {
            "allowed": ["ocean", "stream", "plain", "swamp"],
            "preferred": ["ocean", "stream"],
            "forbidden": ["mountain", "hill", "forest", "desert"]
        },
        "plain": {
            "allowed": ["plain", "hill", "stream", "ocean", "mountain", "forest", "desert", "swamp"],
            "preferred": ["plain", "hill", "forest"],
            "forbidden": []
        },
        "hill": {
            "allowed": ["plain", "hill", "mountain", "stream", "forest"],
            "preferred": ["hill", "mountain"],
            "forbidden": ["ocean", "desert"]
        },
        "mountain": {
            "allowed": ["mountain", "hill", "plain"],
            "preferred": ["mountain", "hill"],
            "forbidden": ["ocean", "stream", "swamp", "desert"]
        },
        "stream": {
            "allowed": ["stream", "plain", "ocean", "hill", "swamp"],
            "preferred": ["stream", "ocean", "plain"],
            "forbidden": ["mountain", "desert"]
        },
        "forest": {
            "allowed": ["plain", "hill", "forest", "stream"],
            "preferred": ["forest", "plain"],
            "forbidden": ["ocean", "mountain", "desert"]
        },
        "desert": {
            "allowed": ["plain", "desert"],
            "preferred": ["desert", "plain"],
            "forbidden": ["ocean", "stream", "hill", "mountain", "forest", "swamp"]
        },
        "swamp": {
            "allowed": ["plain", "stream", "ocean", "swamp"],
            "preferred": ["swamp", "stream"],
            "forbidden": ["mountain", "hill", "desert"]
        }
    }

    def __init__(self, width: int, height: int, cs: CoordinateSystem, persistence: CoordinateSystemPersistence):
        self.width = width
        self.height = height
        self.cs = cs
        self.persistence = persistence
        self.resources = {}
        self.hex_terrain = {}
        self.generate_map()

    def get_neighbors(self, q: int, r: int) -> List[Tuple[int, int]]:
        neighbors = [
            (q+1, r), (q-1, r), (q, r+1), (q, r-1),
            (q+1, r-1), (q-1, r+1)
        ]
        return [(nq, nr) for nq, nr in neighbors
                if -self.width // 2 <= nq <= self.width // 2 and -self.height // 2 <= nr <= self.height // 2]

    def apply_terrain_rules(self, q: int, r: int, terrain: str) -> str:
        neighbors = self.get_neighbors(q, r)
        neighbor_terrains = [self.hex_terrain.get(f"hex_{nq}_{nr}", "plain") for nq, nr in neighbors]
        
        rules = self.TERRAIN_RULES[terrain]
        for nt in neighbor_terrains:
            if nt in rules["forbidden"]:
                forbidden_rules = self.TERRAIN_RULES[nt]
                preferred = forbidden_rules["preferred"]
                weights = [TerrainType.TYPES[t]["weight"] for t in preferred]
                return random.choices(preferred, weights=weights, k=1)[0]
        
        allowed = rules["allowed"]
        if not all(nt in allowed for nt in neighbor_terrains):
            preferred = rules["preferred"]
            weights = [TerrainType.TYPES[t]["weight"] for t in preferred]
            return random.choices(preferred, weights=weights, k=1)[0]
        
        return terrain

    def generate_map(self):
        seeds = [(random.randint(-self.width // 2, self.width // 2),
                  random.randint(-self.height // 2, self.height // 2)) for _ in range(20)]
        terrain_assign = {s: random.choice(list(TerrainType.TYPES.keys())) for s in seeds}

        # Step 1: Assign initial terrains
        for q in range(-self.width // 2, self.width // 2 + 1):
            for r in range(-self.height // 2, self.height // 2 + 1):
                min_dist = float('inf')
                closest = "plain"
                for sq, sr in seeds:
                    dist = max(abs(q - sq), abs(r - sr), abs((q + r) - (sq + sr)))
                    if dist < min_dist:
                        min_dist = dist
                        closest = terrain_assign[(sq, sr)]
                if random.random() < 0.1:
                    closest = random.choices(
                        list(TerrainType.TYPES.keys()),
                        weights=[t["weight"] for t in TerrainType.TYPES.values()],
                        k=1
                    )[0]
                hex_id = f"hex_{q}_{r}"
                self.hex_terrain[hex_id] = closest

        # Step 2: Apply terrain rules
        for q in range(-self.width // 2, self.width // 2 + 1):
            for r in range(-self.height // 2, self.height // 2 + 1):
                hex_id = f"hex_{q}_{r}"
                terrain = self.hex_terrain[hex_id]
                new_terrain = self.apply_terrain_rules(q, r, terrain)
                self.hex_terrain[hex_id] = new_terrain

        # Step 3: Collect hexes
        hexes = []
        for q in range(-self.width // 2, self.width // 2 + 1):
            for r in range(-self.height // 2, self.height // 2 + 1):
                hex_id = f"hex_{q}_{r}"
                terrain = self.hex_terrain[hex_id]
                vertices = HexUtils.get_hex_vertices(q, r, Config.HEX_SIZE)
                hexes.append((hex_id, vertices, terrain))

        # Define rendering priority (higher priority renders LAST, on top)
        terrain_priority = {
            "ocean": 8,    # Render last (on top)
            "swamp": 7,    # Watery terrain, high priority
            "stream": 6,
            "mountain": 5,
            "hill": 4,
            "forest": 3,   # Trees above plains but below hills
            "desert": 2,
            "plain": 1     # Render first (in the back)
        }

        # Sort hexes by terrain priority (ascending order, so plains added first, oceans last)
        hexes.sort(key=lambda x: terrain_priority.get(x[2], 1))  # Default to plain priority if terrain not found

        # Step 4: Add sorted hexes to CoordinateSystem
        for hex_id, vertices, terrain in hexes:
            self.cs.add_static_polygon(hex_id, vertices, category=terrain)

        # Step 5: Add resources
        for q in range(-self.width // 2, self.width // 2 + 1):
            for r in range(-self.height // 2, self.height // 2 + 1):
                hex_id = f"hex_{q}_{r}"
                terrain = self.hex_terrain[hex_id]
                if random.random() < 0.1 and terrain not in ["ocean", "mountain", "swamp"]:
                    resource_pos = HexUtils.hex_to_cartesian(q, r, Config.HEX_SIZE)
                    self.cs.add_entity(f"resource_{q}_{r}", resource_pos)
                    self.resources[f"resource_{q}_{r}"] = random.choice(list(ResourceType.TYPES.keys()))

        self.persistence.save_coordinate_system(self.cs)