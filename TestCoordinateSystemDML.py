import unittest
import os
import sqlite3
from CoordinateSystem import CoordinateSystem
from CoordinateSystemPersistence import CoordinateSystemPersistence
from CoordinateSystemDML import CoordinateSystemDML

class TestCoordinateSystemDML(unittest.TestCase):
    def setUp(self):
        self.db_name = "test_db"
        self.db_path = f"{self.db_name}.db"
        self.cs = CoordinateSystem()
        self.cs.add_entity("player_1", (1.1, 0.0, 0.0))
        self.cs.add_entity("npc_42", (2.0, 2.0, 2.0))
        self.cs.add_entity("object_7", (3.0, 3.0, 3.0))
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "ground_plane")
        self.cs.add_static_polygon("wall1", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], "wall")
        self.persistence = CoordinateSystemPersistence(self.db_name)
        self.persistence.save_coordinate_system(self.cs)
        self.dml = CoordinateSystemDML(self.db_name)
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
        with self.assertRaises(FileNotFoundError):
            CoordinateSystemDML("nonexistent_db")
        cursor = self.dml.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("entities", tables)
        self.assertIn("geometry", tables)

    def test_count_entities(self):
        self.assertEqual(self.dml.count_entities(), 3)
        counts = self.dml.count_entities("player")
        self.assertEqual(counts, {"player": 1})
        counts = self.dml.count_entities("npc")
        self.assertEqual(counts, {"npc": 1})
        counts = self.dml.count_entities("object")
        self.assertEqual(counts, {"object": 1})
        counts = self.dml.count_entities("invalid")
        self.assertEqual(counts, {})

    def test_list_entities_in_bounding_box(self):
        entities = self.dml.list_entities_in_bounding_box((0.0, 0.0, 0.0), (1.5, 1.5, 1.5))
        self.assertEqual(entities, {"player_1": (1.1, 0.0, 0.0)})
        entities = self.dml.list_entities_in_bounding_box((0.0, 0.0, 0.0), (3.0, 3.0, 3.0))
        self.assertEqual(len(entities), 3)
        self.assertIn("player_1", entities)
        self.assertIn("npc_42", entities)
        self.assertIn("object_7", entities)
        entities = self.dml.list_entities_in_bounding_box((4.0, 4.0, 4.0), (5.0, 5.0, 5.0))
        self.assertEqual(entities, {})
        with self.assertRaises(ValueError):
            self.dml.list_entities_in_bounding_box((2.0, 0.0, 0.0), (1.0, 1.0, 1.0))

    def test_find_nearest_entity(self):
        nearest = self.dml.find_nearest_entity((1.0, 0.0, 0.0))
        self.assertEqual(nearest, ("player_1", (1.1, 0.0, 0.0)))
        nearest = self.dml.find_nearest_entity((1.0, 1.0, 1.0), "npc")
        self.assertEqual(nearest, ("npc_42", (2.0, 2.0, 2.0)))
        nearest = self.dml.find_nearest_entity((1.0, 1.0, 1.0), "invalid")
        self.assertIsNone(nearest)
        empty_persistence = CoordinateSystemPersistence("empty_db")
        empty_persistence.save_coordinate_system(CoordinateSystem())
        empty_dml = CoordinateSystemDML("empty_db")
        nearest = empty_dml.find_nearest_entity((1.0, 1.0, 1.0))
        self.assertIsNone(nearest)

    def test_list_geometry_by_category(self):
        ground = self.dml.list_geometry_by_category("ground_plane")
        self.assertEqual(ground, {
            "ground": {
                "type": "plane",
                "origin": (0.0, 0.0, 0.0),
                "normal": (0.0, 0.0, 1.0),
                "category": "ground_plane"
            }
        })
        walls = self.dml.list_geometry_by_category("wall")
        self.assertEqual(walls["wall1"]["type"], "polygon")
        self.assertEqual(walls["wall1"]["vertices"], [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)])
        self.assertEqual(walls["wall1"]["category"], "wall")
        empty = self.dml.list_geometry_by_category("invalid")
        self.assertEqual(empty, {})

    def test_is_entity_near_geometry(self):
        self.assertTrue(self.dml.is_entity_near_geometry("player_1", "wall", 0.2))
        self.assertFalse(self.dml.is_entity_near_geometry("player_1", "wall", 0.0))
        self.assertTrue(self.dml.is_entity_near_geometry("player_1", "ground_plane", 1.0))
        self.assertFalse(self.dml.is_entity_near_geometry("player_1", "invalid", 1.0))
        with self.assertRaises(KeyError):
            self.dml.is_entity_near_geometry("nonexistent", "wall", 1.0)

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