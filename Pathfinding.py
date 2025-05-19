from typing import List, Dict
from CoordinateSystem import Coordinate3D, CoordinateSystem
from CoordinateSystemDML import CoordinateSystemDML
from TerrainType import TerrainType
from HexUtils import HexUtils
from Config import Config

class Pathfinding:
    @staticmethod
    def hex_distance(a: Coordinate3D, b: Coordinate3D) -> float:
        q1, r1 = HexUtils.cartesian_to_hex(a[0], a[1], Config.HEX_SIZE)
        q2, r2 = HexUtils.cartesian_to_hex(b[0], b[1], Config.HEX_SIZE)
        return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2)))

    @staticmethod
    def get_neighbors(pos: Coordinate3D, cs: CoordinateSystem, dml: CoordinateSystemDML) -> List[Coordinate3D]:
        q, r = HexUtils.cartesian_to_hex(pos[0], pos[1], Config.HEX_SIZE)
        neighbors = [
            (q+1, r), (q-1, r), (q, r+1), (q, r-1),
            (q+1, r-1), (q-1, r+1)
        ]
        return [HexUtils.hex_to_cartesian(nq, nr, Config.HEX_SIZE) for nq, nr in neighbors
                if cs.get_static_geometry(f"hex_{nq}_{nr}") is not None]

    @staticmethod
    def a_star(start: Coordinate3D, goal: Coordinate3D, cs: CoordinateSystem, dml: CoordinateSystemDML) -> List[Coordinate3D]:
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: Pathfinding.hex_distance(start, goal)}
        
        while open_set:
            current_f, current = open_set.pop(0)  # Replaced heappop with sorted list pop
            # Relaxed goal check using hex distance
            if Pathfinding.hex_distance(current, goal) < 1.0:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]
                
            for neighbor in Pathfinding.get_neighbors(current, cs, dml):
                q, r = HexUtils.cartesian_to_hex(neighbor[0], neighbor[1], Config.HEX_SIZE)
                hex_id = f"hex_{q}_{r}"
                terrain = cs.get_static_geometry(hex_id)
                if not terrain:
                    continue
                move_cost = TerrainType.TYPES[terrain["category"]]["move_cost"]
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + Pathfinding.hex_distance(neighbor, goal)
                    open_set.append((f_score[neighbor], neighbor))
                    open_set.sort()  # Sort the list to mimic heap behavior
        return []