import unittest
import os
import sqlite3
from datetime import datetime
from CoordinateSystem import CoordinateSystem
from CoordinateSystemPersistence import CoordinateSystemPersistence

class TestCoordinateSystemPersistence(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_db"
        self.db_path = f"{self.db_name}.db"
        self.persistence = CoordinateSystemPersistence(self.db_name)
        self.cs = CoordinateSystem()
        print(f"\nStarting test: {self._testMethodName}")

    def tearDown(self):
        result = self._outcome.result
        test_id = f"{self.__class__.__name__}.{self._testMethodName}"
        for test, _ in result.failures + result.errors:
            if test.id() == test_id:
                status = "FAILED" if test in [t for t, _ in result.failures] else "ERROR"
                print(f"Test {self._testMethodName}: {status}")
                return
        if result.skipped:
            for test, _ in result.skipped:
                if test.id() == test_id:
                    print(f"Test {self._testMethodName}: SKIPPED")
                    return
        print(f"Test {self._testMethodName}: PASSED")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init(self):
        self.assertTrue(os.path.exists(self.db_path))
        with sqlite3.connect(self.db_path) as conn:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [t[0] for t in tables]
            self.assertIn("entities", table_names)
            self.assertIn("geometry", table_names)
            self.assertIn("metadata", table_names)
            created_at = conn.execute("SELECT value FROM metadata WHERE key = ?", ("created_at",)).fetchone()
            self.assertIsNotNone(created_at)
            self.assertTrue(datetime.fromisoformat(created_at[0]))  # Valid ISO format

    def test_save_coordinate_system(self):
        self.cs.add_entity("player1", (1.0, 2.0, 3.0))
        self.cs.add_entity("npc1", (4.0, 5.0, 6.0))
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "ground_plane")
        self.cs.add_static_polygon("wall1", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], "wall")
        self.persistence.save_coordinate_system(self.cs)
        with sqlite3.connect(self.db_path) as conn:
            entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            geometry_count = conn.execute("SELECT COUNT(*) FROM geometry").fetchone()[0]
            last_saved = conn.execute("SELECT value FROM metadata WHERE key = ?", ("last_saved_at",)).fetchone()
            self.assertEqual(entity_count, 2)
            self.assertEqual(geometry_count, 2)
            self.assertIsNotNone(last_saved)
            self.assertTrue(datetime.fromisoformat(last_saved[0]))
            player_pos = conn.execute("SELECT x, y, z FROM entities WHERE id = ?", ("player1",)).fetchone()
            self.assertEqual(player_pos, (1.0, 2.0, 3.0))

    def test_load_coordinate_system(self):
        self.cs.add_entity("player1", (1.0, 2.0, 3.0))
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "ground_plane")
        self.persistence.save_coordinate_system(self.cs)
        loaded_cs = self.persistence.load_coordinate_system()
        self.assertEqual(loaded_cs.get_entity_position("player1"), (1.0, 2.0, 3.0))
        ground = loaded_cs.get_static_geometry("ground")
        self.assertEqual(ground, {
            "type": "plane",
            "origin": (0.0, 0.0, 0.0),
            "normal": (0.0, 0.0, 1.0),
            "category": "ground_plane"
        })
        empty_persistence = CoordinateSystemPersistence("empty_db")
        empty_cs = empty_persistence.load_coordinate_system()
        self.assertEqual(empty_cs.get_all_entity_positions(), {})
        self.assertEqual(empty_cs.list_all_static_geometry(), {})

    def test_get_database_info(self):
        info = self.persistence.get_database_info()
        self.assertEqual(info["db_name"], self.db_name)
        self.assertIsNotNone(info["created_at"])
        self.assertTrue(datetime.fromisoformat(info["created_at"]))
        self.assertIsNone(info["last_saved_at"])
        self.assertEqual(info["entity_count"], 0)
        self.assertEqual(info["geometry_count"], 0)
        self.cs.add_entity("player1", (1.0, 2.0, 3.0))
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        self.persistence.save_coordinate_system(self.cs)
        info = self.persistence.get_database_info()
        self.assertIsNotNone(info["last_saved_at"])
        self.assertTrue(datetime.fromisoformat(info["last_saved_at"]))
        self.assertEqual(info["entity_count"], 1)
        self.assertEqual(info["geometry_count"], 1)

if __name__ == "__main__":
    result = unittest.main(verbosity=0, exit=False).result
    print("\n=== Final Test Summary ===")
    print(f"Total tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    if result.failures or result.errors:
        print("\nDetails of Failures/Errors:")
        for test, err in result.failures + result.errors:
            print(f"{test.id()}: {err}")
    else:
        print("All tests passed successfully!")