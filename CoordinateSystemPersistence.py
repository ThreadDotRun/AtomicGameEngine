import sqlite3
import json
from datetime import datetime
from typing import Dict, Any
from CoordinateSystem import CoordinateSystem, Coordinate3D, EntityID, GeometryID

class CoordinateSystemPersistence:
    def __init__(self, db_name: str):
        self.db_path = f"{db_name}.db"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS entities (id TEXT PRIMARY KEY, x REAL, y REAL, z REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS geometry (id TEXT PRIMARY KEY, type TEXT, data TEXT, category TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("INSERT OR IGNORE INTO metadata (key, value) VALUES (?, ?)", 
                        ("created_at", datetime.utcnow().isoformat()))

    def save_coordinate_system(self, cs: CoordinateSystem) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM entities")
            conn.execute("DELETE FROM geometry")
            for eid, (x, y, z) in cs.get_all_entity_positions().items():
                conn.execute("INSERT INTO entities (id, x, y, z) VALUES (?, ?, ?, ?)", 
                            (str(eid), x, y, z))
            for gid, gdata in cs.list_all_static_geometry().items():
                data_json = json.dumps({
                    "origin": gdata["origin"] if gdata["type"] == "plane" else None,
                    "normal": gdata["normal"] if gdata["type"] == "plane" else None,
                    "vertices": gdata["vertices"] if gdata["type"] == "polygon" else None
                })
                conn.execute("INSERT INTO geometry (id, type, data, category) VALUES (?, ?, ?, ?)",
                            (gid, gdata["type"], data_json, gdata["category"]))
            conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
                        ("last_saved_at", datetime.utcnow().isoformat()))
            conn.commit()

    def load_coordinate_system(self) -> CoordinateSystem:
        cs = CoordinateSystem()
        with sqlite3.connect(self.db_path) as conn:
            for row in conn.execute("SELECT id, x, y, z FROM entities"):
                cs.add_entity(row[0], (row[1], row[2], row[3]))
            for row in conn.execute("SELECT id, type, data, category FROM geometry"):
                data = json.loads(row[2])
                if row[1] == "plane":
                    cs.add_static_plane(row[0], tuple(data["origin"]), tuple(data["normal"]), row[3])
                elif row[1] == "polygon":
                    cs.add_static_polygon(row[0], [tuple(v) for v in data["vertices"]], row[3])
        return cs

    def get_database_info(self) -> Dict[str, Any]:
        info = {"db_name": self.db_path[:-3], "created_at": None, "last_saved_at": None, 
                "entity_count": 0, "geometry_count": 0}
        with sqlite3.connect(self.db_path) as conn:
            for row in conn.execute("SELECT value FROM metadata WHERE key = ?", ("created_at",)):
                info["created_at"] = row[0]
            for row in conn.execute("SELECT value FROM metadata WHERE key = ?", ("last_saved_at",)):
                info["last_saved_at"] = row[0]
            for row in conn.execute("SELECT COUNT(*) FROM entities"):
                info["entity_count"] = row[0]
            for row in conn.execute("SELECT COUNT(*) FROM geometry"):
                info["geometry_count"] = row[0]
        return info