import unittest
from CoordinateSystem import CoordinateSystem, Coordinate3D, EntityID, GeometryID
from typing import List, Dict, Any
import os

class TestCoordinateSystem(unittest.TestCase):
    def setUp(self):
        print(f"\nStarting test: {self._testMethodName}")
        self.cs = CoordinateSystem()

    def tearDown(self):
        # Check the result of the test by inspecting the test case's state
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

    def test_get_version(self):
        version = self.cs.get_version()
        self.assertIsInstance(version, str)
        self.assertTrue(version == "unknown version" or os.path.exists(os.path.join(os.path.dirname(__file__), "version.txt")))

    def test_get_info_message(self):
        info = self.cs.get_info_message()
        self.assertIsInstance(info, str)
        self.assertTrue(len(info) > 0)

    def test_add_entity(self):
        self.cs.add_entity("player1", (1.0, 2.0, 3.0))
        self.assertEqual(self.cs.get_entity_position("player1"), (1.0, 2.0, 3.0))
        self.cs.add_entity("player1", (4.0, 5.0, 6.0))
        self.assertEqual(self.cs.get_entity_position("player1"), (4.0, 5.0, 6.0))
        with self.assertRaises(TypeError):
            self.cs.add_entity("player2", (1, 2))

    def test_remove_entity(self):
        self.cs.add_entity("player1", (1.0, 2.0, 3.0))
        self.cs.remove_entity("player1")
        self.assertIsNone(self.cs.get_entity_position("player1"))
        with self.assertRaises(KeyError):
            self.cs.remove_entity("nonexistent")

    def test_update_entity_position(self):
        self.cs.add_entity("player1", (1.0, 2.0, 3.0))
        self.cs.update_entity_position("player1", (7.0, 8.0, 9.0))
        self.assertEqual(self.cs.get_entity_position("player1"), (7.0, 8.0, 9.0))
        with self.assertRaises(KeyError):
            self.cs.update_entity_position("nonexistent", (1.0, 2.0, 3.0))
        with self.assertRaises(TypeError):
            self.cs.update_entity_position("player1", (1, 2))

    def test_get_entity_position(self):
        self.cs.add_entity("player1", (1.0, 2.0, 3.0))
        self.assertEqual(self.cs.get_entity_position("player1"), (1.0, 2.0, 3.0))
        self.assertIsNone(self.cs.get_entity_position("nonexistent"))

    def test_get_all_entity_positions(self):
        self.cs.add_entity("player1", (1.0, 2.0, 3.0))
        self.cs.add_entity("npc1", (4.0, 5.0, 6.0))
        positions = self.cs.get_all_entity_positions()
        self.assertEqual(positions, {"player1": (1.0, 2.0, 3.0), "npc1": (4.0, 5.0, 6.0)})
        self.cs.remove_entity("player1")
        positions = self.cs.get_all_entity_positions()
        self.assertEqual(positions, {"npc1": (4.0, 5.0, 6.0)})

    def test_add_static_plane(self):
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "ground_plane")
        plane = self.cs.get_static_geometry("ground")
        self.assertEqual(plane, {
            "type": "plane",
            "origin": (0.0, 0.0, 0.0),
            "normal": (0.0, 0.0, 1.0),
            "category": "ground_plane"
        })
        with self.assertRaises(ValueError):
            self.cs.add_static_plane("ground", (1.0, 1.0, 1.0), (0.0, 1.0, 0.0))
        with self.assertRaises(TypeError):
            self.cs.add_static_plane("new_plane", (1, 2), (0, 1, 0))

    def test_add_static_polygon(self):
        vertices = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        self.cs.add_static_polygon("wall1", vertices, "wall")
        polygon = self.cs.get_static_geometry("wall1")
        self.assertEqual(polygon, {
            "type": "polygon",
            "vertices": vertices,
            "category": "wall"
        })
        with self.assertRaises(ValueError):
            self.cs.add_static_polygon("wall1", vertices)
        with self.assertRaises(ValueError):
            self.cs.add_static_polygon("wall2", [(0, 0, 0), (1, 0, 0)])
        with self.assertRaises(TypeError):
            self.cs.add_static_polygon("wall3", [(0, 0), (1, 0, 0), (0, 1, 0)])

    def test_get_static_geometry(self):
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        self.assertIsNotNone(self.cs.get_static_geometry("ground"))
        self.assertIsNone(self.cs.get_static_geometry("nonexistent"))

    def test_remove_static_geometry(self):
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        self.cs.remove_static_geometry("ground")
        self.assertIsNone(self.cs.get_static_geometry("ground"))
        with self.assertRaises(KeyError):
            self.cs.remove_static_geometry("nonexistent")

    def test_list_static_geometry_by_category(self):
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "ground_plane")
        self.cs.add_static_polygon("wall1", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], "wall")
        grounds = self.cs.list_static_geometry_by_category("ground_plane")
        walls = self.cs.list_static_geometry_by_category("wall")
        self.assertEqual(len(grounds), 1)
        self.assertEqual(len(walls), 1)
        self.assertEqual(len(self.cs.list_static_geometry_by_category("nonexistent")), 0)

    def test_list_all_static_geometry(self):
        self.cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "ground_plane")
        self.cs.add_static_polygon("wall1", [(0, 0, 0), (1, 0, 0), (0, 1, 0)], "wall")
        all_geom = self.cs.list_all_static_geometry()
        self.assertEqual(len(all_geom), 2)
        self.assertIn("ground", all_geom)
        self.assertIn("wall1", all_geom)

if __name__ == "__main__":
    unittest.main()