import math
import random
import json
from typing import Optional, List, Tuple, Dict
from CoordinateSystem import CoordinateSystem, Coordinate3D, EntityID
from CoordinateSystemDML import CoordinateSystemDML
from CoordinateSystemPersistence import CoordinateSystemPersistence
from Config import Config
import sqlite3

class CombatSystem:
    """Manages combat interactions between entities in the game engine."""

    def __init__(self, cs: CoordinateSystem, dml: CoordinateSystemDML, persistence: CoordinateSystemPersistence):
        """
        Initialize the CombatSystem with references to core engine components.

        Args:
            cs: CoordinateSystem for entity position management.
            dml: CoordinateSystemDML for spatial queries.
            persistence: CoordinateSystemPersistence for saving combat outcomes.
        """
        self.cs = cs
        self.dml = dml
        self.persistence = persistence
        self.init_combat_table()

    def init_combat_table(self) -> None:
        """Initialize the combat table in the SQLite database for storing entity attributes."""
        with self.persistence.conn:
            self.persistence.conn.execute("""
                CREATE TABLE IF NOT EXISTS combat (
                    entity_id TEXT PRIMARY KEY,
                    health REAL DEFAULT 100.0,
                    attack_power REAL DEFAULT 20.0,
                    defense REAL DEFAULT 10.0,
                    status_effects TEXT DEFAULT '{}',
                    FOREIGN KEY (entity_id) REFERENCES entities(id)
                )
            """)
            self.persistence.conn.commit()

    def update_combat_attributes(self, entity_id: EntityID, health: float = None, attack_power: float = None,
                                 defense: float = None, status_effects: Dict[str, int] = None) -> None:
        """
        Update or initialize combat attributes for an entity in the database.

        Args:
            entity_id: ID of the entity.
            health: Health value to set (optional).
            attack_power: Attack power to set (optional).
            defense: Defense value to set (optional).
            status_effects: Dictionary of status effects and durations (optional).

        Raises:
            KeyError: If entity_id is not found in the coordinate system.
        """
        if not self.cs.get_entity_position(entity_id):
            raise KeyError(f"Entity with ID '{entity_id}' not found.")
        
        with self.persistence.conn:
            cursor = self.persistence.conn.cursor()
            cursor.execute("SELECT health, attack_power, defense, status_effects FROM combat WHERE entity_id = ?",
                           (entity_id,))
            existing = cursor.fetchone()
            
            if existing:
                current_health, current_attack, current_defense, current_effects = existing
                current_effects = json.loads(current_effects)
                health = health if health is not None else current_health
                attack_power = attack_power if attack_power is not None else current_attack
                defense = defense if defense is not None else current_defense
                status_effects = status_effects if status_effects is not None else current_effects
            else:
                health = health if health is not None else 100.0
                attack_power = attack_power if attack_power is not None else 20.0
                defense = defense if defense is not None else 10.0
                status_effects = status_effects if status_effects is not None else {}
            
            cursor.execute("""
                INSERT OR REPLACE INTO combat (entity_id, health, attack_power, defense, status_effects)
                VALUES (?, ?, ?, ?, ?)
            """, (entity_id, health, attack_power, defense, json.dumps(status_effects)))
            self.persistence.conn.commit()

    def get_combat_attributes(self, entity_id: EntityID) -> Optional[Dict[str, any]]:
        """
        Retrieve combat attributes for an entity.

        Args:
            entity_id: ID of the entity.

        Returns:
            Dictionary with health, attack_power, defense, and status_effects, or None if not found.
        """
        with self.persistence.conn:
            cursor = self.persistence.conn.cursor()
            cursor.execute("SELECT health, attack_power, defense, status_effects FROM combat WHERE entity_id = ?",
                           (entity_id,))
            result = cursor.fetchone()
            if result:
                health, attack_power, defense, status_effects = result
                return {
                    "health": health,
                    "attack_power": attack_power,
                    "defense": defense,
                    "status_effects": json.loads(status_effects)
                }
        return None

    def find_targets_in_range(self, attacker_id: EntityID, attack_range: float) -> List[Tuple[EntityID, Coordinate3D]]:
        """
        Find all entities within the attacker's combat range.

        Args:
            attacker_id: ID of the attacking entity.
            attack_range: Maximum distance for valid targets.

        Returns:
            List of tuples (target_id, target_position) for valid targets.

        Raises:
            KeyError: If attacker_id is not found.
            ValueError: If attack_range is negative.
        """
        if attack_range < 0:
            raise ValueError("Attack range must be non-negative.")
        attacker_pos = self.cs.get_entity_position(attacker_id)
        if not attacker_pos:
            raise KeyError(f"Attacker with ID '{attacker_id}' not found.")

        # Use DML to find entities within range
        nearest = self.dml.find_nearest_entity(attacker_pos, max_distance=attack_range)
        if nearest and nearest[0] != attacker_id:
            return [nearest]
        return []

    def resolve_combat(self, attacker_id: EntityID, defender_id: EntityID) -> bool:
        """
        Resolve a single combat action between attacker and defender.

        Args:
            attacker_id: ID of the attacking entity.
            defender_id: ID of the defending entity.

        Returns:
            True if defender is defeated (health <= 0), False otherwise.

        Raises:
            KeyError: If attacker or defender is not found.
            ValueError: If combat attributes are missing.
        """
        attacker_attrs = self.get_combat_attributes(attacker_id)
        defender_attrs = self.get_combat_attributes(defender_id)
        
        if not attacker_attrs or not defender_attrs:
            raise ValueError(f"Combat attributes missing for {attacker_id} or {defender_id}.")

        # Check for status effects
        if attacker_attrs["status_effects"].get("stunned", 0) > 0:
            return False  # Attacker cannot attack while stunned

        # Calculate damage (simple formula: attack - defense/2, minimum 1)
        damage = max(1.0, attacker_attrs["attack_power"] - defender_attrs["defense"] * 0.5)
        
        # Apply damage
        new_health = max(0.0, defender_attrs["health"] - damage)
        self.update_combat_attributes(defender_id, health=new_health)
        
        if new_health <= 0:
            self.cs.remove_entity(defender_id)
            with self.persistence.conn:
                self.persistence.conn.execute("DELETE FROM combat WHERE entity_id = ?", (defender_id,))
            self.persistence.save_coordinate_system(self.cs)
            return True
        return False

    def initiate_combat(self, attacker_id: EntityID, target_id: EntityID) -> bool:
        """
        Initiate combat between two entities, checking range and resolving outcome.

        Args:
            attacker_id: ID of the attacking entity.
            target_id: ID of the target entity.

        Returns:
            True if target is defeated, False otherwise.

        Raises:
            KeyError: If attacker or target is not found.
            ValueError: If target is out of range.
        """
        attacker_pos = self.cs.get_entity_position(attacker_id)
        target_pos = self.cs.get_entity_position(target_id)
        if not attacker_pos or not target_pos:
            raise KeyError("Attacker or target not found in coordinate system.")

        # Check if target is within default attack range (1 hex)
        distance = math.sqrt(sum((attacker_pos[i] - target_pos[i]) ** 2 for i in range(3)))
        default_range = Config.HEX_SIZE * 1.5  # Approx. 1 hex distance
        if distance > default_range:
            raise ValueError(f"Target {target_id} is out of attack range for {attacker_id}.")

        return self.resolve_combat(attacker_id, target_id)

    def apply_status_effect(self, entity_id: EntityID, effect: str, duration: int) -> None:
        """
        Apply a status effect to an entity (e.g., 'stunned', 'poisoned').

        Args:
            entity_id: ID of the affected entity.
            effect: Name of the status effect.
            duration: Number of turns the effect lasts.

        Raises:
            KeyError: If entity is not found.
            ValueError: If duration is negative or effect is invalid.
        """
        valid_effects = ['stunned', 'poisoned', 'buffed']
        if effect not in valid_effects:
            raise ValueError(f"Invalid status effect: {effect}. Valid effects: {valid_effects}")
        if duration < 0:
            raise ValueError("Duration must be non-negative.")
        
        if not self.cs.get_entity_position(entity_id):
            raise KeyError(f"Entity with ID '{entity_id}' not found.")
        
        attrs = self.get_combat_attributes(entity_id) or {}
        status_effects = attrs.get("status_effects", {})
        status_effects[effect] = duration
        self.update_combat_attributes(entity_id, status_effects=status_effects)

    def update_status_effects(self, entity_id: EntityID) -> None:
        """
        Update status effects for an entity, applying effects like poison and removing expired effects.

        Args:
            entity_id: ID of the entity.

        Raises:
            KeyError: If entity is not found.
        """
        attrs = self.get_combat_attributes(entity_id)
        if not attrs:
            return
        
        status_effects = attrs["status_effects"]
        new_effects = {}
        for effect, duration in status_effects.items():
            new_duration = duration - 1
            if new_duration > 0:
                new_effects[effect] = new_duration
            if effect == "poisoned" and attrs["health"] > 0:
                new_health = max(0.0, attrs["health"] - 5.0)
                attrs["health"] = new_health
                if new_health <= 0:
                    self.cs.remove_entity(entity_id)
                    with self.persistence.conn:
                        self.persistence.conn.execute("DELETE FROM combat WHERE entity_id = ?", (entity_id,))
                    self.persistence.save_coordinate_system(self.cs)
                    return
        
        self.update_combat_attributes(entity_id, health=attrs["health"], status_effects=new_effects)