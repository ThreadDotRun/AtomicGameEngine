import unittest
import sqlite3
import json
import os
from CoordinateSystem import CoordinateSystem
from CoordinateSystemPersistence import CoordinateSystemPersistence
from CoordinateSystemDML import CoordinateSystemDML
from CombatSystem import CombatSystem
from Config import Config

class TestCombatSystem(unittest.TestCase):
    def setUp(self):
        self.cs = CoordinateSystem()
        self.persistence = CoordinateSystemPersistence("test_combat_db")
        self.dml = CoordinateSystemDML(self.persistence.conn)
        self.combat_system = CombatSystem(self.cs, self.dml, self.persistence)
        self.cs.add_entity("unit_1", (0.0, 0.0, 0.0))
        self.cs.add_entity("unit_2", (Config.HEX_SIZE, Config.HEX_SIZE, 0.0))
        self.persistence.save_coordinate_system(self.cs)  # Save to DB for DML queries
        self.combat_system.update_combat_attributes("unit_1")
        self.combat_system.update_combat_attributes("unit_2")
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
        if self.persistence.db_path != ":memory:" and os.path.exists(self.persistence.db_path):
            os.remove(self.persistence.db_path)

    def test_init_combat_table(self):
        with self.persistence.conn:
            tables = self.persistence.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            table_names = [t[0] for t in tables]
            self.assertIn("combat", table_names)

    def test_update_combat_attributes(self):
        self.combat_system.update_combat_attributes("unit_1", health=50.0, attack_power=30.0, defense=15.0)
        attrs = self.combat_system.get_combat_attributes("unit_1")
        self.assertEqual(attrs["health"], 50.0)
        self.assertEqual(attrs["attack_power"], 30.0)
        self.assertEqual(attrs["defense"], 15.0)
        self.assertEqual(attrs["status_effects"], {})
        with self.assertRaises(KeyError):
            self.combat_system.update_combat_attributes("nonexistent")

    def test_find_targets_in_range(self):
        targets = self.combat_system.find_targets_in_range("unit_1", Config.ATTACK_RANGE)
        self.assertEqual(len(targets), 1, f"Expected 1 target, got {targets}")
        self.assertEqual(targets[0][0], "unit_2")
        targets = self.combat_system.find_targets_in_range("unit_1", Config.HEX_SIZE / 2)
        self.assertEqual(targets, [])
        with self.assertRaises(KeyError):
            self.combat_system.find_targets_in_range("nonexistent", Config.ATTACK_RANGE)

    def test_resolve_combat(self):
        defeated = self.combat_system.resolve_combat("unit_1", "unit_2")
        attrs = self.combat_system.get_combat_attributes("unit_2")
        self.assertFalse(defeated)
        self.assertLess(attrs["health"], 100.0)
        self.combat_system.update_combat_attributes("unit_2", health=1.0)
        defeated = self.combat_system.resolve_combat("unit_1", "unit_2")
        self.assertTrue(defeated)
        self.assertIsNone(self.cs.get_entity_position("unit_2"))
        with self.assertRaises(KeyError):
            self.combat_system.resolve_combat("nonexistent", "unit_2")

    def test_apply_status_effect(self):
        self.combat_system.apply_status_effect("unit_1", "stunned", 2)
        attrs = self.combat_system.get_combat_attributes("unit_1")
        self.assertEqual(attrs["status_effects"], {"stunned": 2})
        self.combat_system.update_status_effects("unit_1")
        attrs = self.combat_system.get_combat_attributes("unit_1")
        self.assertEqual(attrs["status_effects"], {"stunned": 1})
        with self.assertRaises(ValueError):
            self.combat_system.apply_status_effect("unit_1", "invalid", 2)

if __name__ == "__main__":
    unittest.main()