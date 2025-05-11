import sqlite3
import json
import math
import os
from typing import Tuple, List, Dict, Optional, Union, Any
from CoordinateSystem import Coordinate3D, EntityID, GeometryID

class CoordinateSystemDML:
    def __init__(self, db_name: str):
        self.db_path = f"{db_name}.db"
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file {self.db_path} not found")
        self.conn = sqlite3.connect(self.db_path)

    def count_entities(self, type_prefix: Optional[str] = None) -> Union[int, Dict[str, int]]:
        cursor = self.conn.cursor()
        if type_prefix is None:
            cursor.execute("SELECT COUNT(*) FROM entities")
            return cursor.fetchone()[0]
        cursor.execute("SELECT id FROM entities WHERE id LIKE ?", (f"{type_prefix}%",))
        counts = {}
        for (id,) in cursor.fetchall():
            prefix = id.split("_")[0] if "_" in id else id
            if prefix.startswith(type_prefix):
                counts[prefix] = counts.get(prefix, 0) + 1
        return counts

    def list_entities_in_bounding_box(self, min_coords: Coordinate3D, max_coords: Coordinate3D) -> Dict[EntityID, Coordinate3D]:
        if any(min_coords[i] > max_coords[i] for i in range(3)):
            raise ValueError("min_coords must be less than or equal to max_coords")
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, x, y, z FROM entities WHERE x >= ? AND x <= ? AND y >= ? AND y <= ? AND z >= ? AND z <= ?",
                       (min_coords[0], max_coords[0], min_coords[1], max_coords[1], min_coords[2], max_coords[2]))
        return {row[0]: (row[1], row[2], row[3]) for row in cursor.fetchall()}

    def find_nearest_entity(self, point: Coordinate3D, type_prefix: Optional[str] = None) -> Optional[Tuple[EntityID, Coordinate3D]]:
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

    def list_geometry_by_category(self, category: str) -> Dict[GeometryID, Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, type, data, category FROM geometry WHERE category = ?", (category,))
        result = {}
        for id, type, data, cat in cursor.fetchall():
            data_dict = json.loads(data)
            if type == "plane":
                result[id] = {"type": type, "origin": tuple(data_dict["origin"]), "normal": tuple(data_dict["normal"]), "category": cat}
            else:
                result[id] = {"type": type, "vertices": [tuple(v) for v in data_dict["vertices"]], "category": cat}
        return result

    def is_entity_near_geometry(self, entity_id: EntityID, category: str, max_distance: float) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT x, y, z FROM entities WHERE id = ?", (str(entity_id),))
        pos = cursor.fetchone()
        if not pos:
            raise KeyError(f"Entity with ID '{entity_id}' not found")
        pos = (pos[0], pos[1], pos[2])
        cursor.execute("SELECT type, data FROM geometry WHERE category = ?", (category,))
        for type, data in cursor.fetchall():
            data_dict = json.loads(data)
            if type == "plane":
                normal = tuple(data_dict["normal"])
                origin = tuple(data_dict["origin"])
                dist = abs(sum((pos[i] - origin[i]) * normal[i] for i in range(3))) / math.sqrt(sum(n * n for n in normal))
            else:
                vertices = [tuple(v) for v in data_dict["vertices"]]
                dist = min(math.sqrt(sum((pos[i] - v[i]) ** 2 for i in range(3))) for v in vertices)
            if dist <= max_distance:
                return True
        return False