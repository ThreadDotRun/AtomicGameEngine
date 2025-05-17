import sqlite3
import math
from typing import Dict, Optional, Tuple
from CoordinateSystem import Coordinate3D, EntityID

class CoordinateSystemDML:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_entities_in_bounding_box(self, min_coords: Coordinate3D, max_coords: Coordinate3D) -> Dict[EntityID, Coordinate3D]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id, x, y, z FROM entities WHERE x >= ? AND x <= ? AND y >= ? AND y <= ? AND z >= ? AND z <= ?",
                           (min_coords[0], max_coords[0], min_coords[1], max_coords[1], min_coords[2], max_coords[2]))
            return {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}
        except sqlite3.OperationalError:
            return {}

    def find_nearest_entity(self, point: Coordinate3D, type_prefix: Optional[str] = None) -> Optional[Tuple[EntityID, Coordinate3D]]:
        try:
            cursor = self.conn.cursor()
            query = "SELECT id, x, y, z FROM entities"
            params = []
            if type_prefix:
                query += " WHERE id LIKE ?"
                params.append(f"{type_prefix}%")
            cursor.execute(query, params)
            nearest = None
            min_dist = float("inf")
            for id, x, y, z in cursor.fetchall():
                pos = (x, y, z)
                dist = math.sqrt(sum((point[i] - pos[i]) ** 2 for i in range(3)))
                if dist < min_dist:
                    min_dist = dist
                    nearest = (id, pos)
            return nearest
        except sqlite3.OperationalError:
            return None

    def is_entity_near_geometry(self, entity_id: EntityID, category: str, max_distance: float) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT x, y, z FROM entities WHERE id = ?", (str(entity_id),))
            pos = cursor.fetchone()
            if not pos:
                return False
            pos = (pos[0], pos[1], pos[2])
            cursor.execute("SELECT type, data FROM geometry WHERE category = ?", (category,))
            for type, data in cursor.fetchall():
                data_dict = json.loads(data)
                vertices = [tuple(v) for v in data_dict["vertices"]]
                dist = min(math.sqrt(sum((pos[i] - v[i]) ** 2 for i in range(3))) for v in vertices)
                if dist <= max_distance:
                    return True
            return False
        except sqlite3.OperationalError:
            return False