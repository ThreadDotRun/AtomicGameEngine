import sqlite3
import json
import platform
from CoordinateSystem import CoordinateSystem, Coordinate3D, EntityID, GeometryID
from typing import Dict

class CoordinateSystemPersistence:
    def __init__(self, db_name: str):
        self.db_path = ":memory:" if platform.system() == "Emscripten" else f"{db_name}.db"
        self.conn = sqlite3.connect(self.db_path)
        self.init_tables()

    def init_tables(self):
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS entities (id TEXT PRIMARY KEY, x REAL, y REAL, z REAL)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS geometry (id TEXT PRIMARY KEY, type TEXT, data TEXT, category TEXT)")
            self.conn.commit()

    def save_coordinate_system(self, cs: CoordinateSystem) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM entities")
            self.conn.execute("DELETE FROM geometry")
            for eid, (x, y, z) in cs.get_all_entity_positions().items():
                self.conn.execute("INSERT INTO entities (id, x, y, z) VALUES (?, ?, ?, ?)", (str(eid), x, y, z))
            for gid, gdata in cs.list_all_static_geometry().items():
                data_json = json.dumps({"vertices": gdata["vertices"]})
                self.conn.execute("INSERT INTO geometry (id, type, data, category) VALUES (?, ?, ?, ?)",
                                 (gid, gdata["type"], data_json, gdata["category"]))
            self.conn.commit()

    def load_coordinate_system(self) -> CoordinateSystem:
        cs = CoordinateSystem()
        with self.conn:
            for row in self.conn.execute("SELECT id, x, y, z FROM entities"):
                cs.add_entity(row[0], (row[1], row[2], row[3]))
            for row in self.conn.execute("SELECT id, type, data, category FROM geometry"):
                data = json.loads(row[2])
                if row[1] == "polygon":
                    cs.add_static_polygon(row[0], [tuple(v) for v in data["vertices"]], row[3])
        return cs