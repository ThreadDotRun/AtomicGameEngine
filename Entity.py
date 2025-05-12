from abc import ABC, abstractmethod
from typing import Tuple, Dict, Optional, Any
from CoordinateSystem import CoordinateSystem, Coordinate3D, EntityID, GeometryID
from CoordinateSystemDML import CoordinateSystemDML
from CoordinateSystemPersistence import CoordinateSystemPersistence

class Entity(ABC):
    """Abstract base class for entities in a 3D coordinate system."""
    
    def __init__(
        self,
        entity_id: EntityID,
        position: Coordinate3D,
        coordinate_system: CoordinateSystem,
        dml: Optional[CoordinateSystemDML] = None,
        persistence: Optional[CoordinateSystemPersistence] = None
    ):
        """
        Initialize an Entity with an ID, position, and references to system components.
        
        Args:
            entity_id: Unique identifier for the entity (str or int).
            position: Initial 3D position as a tuple (x, y, z).
            coordinate_system: Instance of CoordinateSystem for position management.
            dml: Optional instance of CoordinateSystemDML for spatial queries.
            persistence: Optional instance of CoordinateSystemPersistence for data storage.
        
        Raises:
            TypeError: If position is not a valid 3D coordinate tuple.
            ValueError: If entity_id is invalid or already exists in the coordinate system.
        """
        self._entity_id = entity_id
        self._coordinate_system = coordinate_system
        self._dml = dml
        self._persistence = persistence
        
        # Validate and set initial position
        try:
            self._coordinate_system.add_entity(self._entity_id, position)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to initialize entity {entity_id}: {str(e)}")

    @property
    def entity_id(self) -> EntityID:
        """Get the entity's unique identifier."""
        return self._entity_id

    @property
    def position(self) -> Optional[Coordinate3D]:
        """Get the entity's current position."""
        return self._coordinate_system.get_entity_position(self._entity_id)

    def update_position(self, new_position: Coordinate3D) -> None:
        """
        Update the entity's position in the coordinate system.
        
        Args:
            new_position: New 3D position as a tuple (x, y, z).
        
        Raises:
            KeyError: If the entity is not found in the coordinate system.
            TypeError: If new_position is not a valid 3D coordinate tuple.
        """
        self._coordinate_system.update_entity_position(self._entity_id, new_position)
        if self._persistence:
            self._persistence.save_coordinate_system(self._coordinate_system)

    def remove(self) -> None:
        """
        Remove the entity from the coordinate system and persist changes.
        
        Raises:
            KeyError: If the entity is not found in the coordinate system.
        """
        self._coordinate_system.remove_entity(self._entity_id)
        if self._persistence:
            self._persistence.save_coordinate_system(self._coordinate_system)

    def get_nearby_entities(
        self, min_coords: Coordinate3D, max_coords: Coordinate3D
    ) -> Dict[EntityID, Coordinate3D]:
        """
        Find entities within a bounding box using CoordinateSystemDML.
        
        Args:
            min_coords: Minimum (x, y, z) coordinates of the bounding box.
            max_coords: Maximum (x, y, z) coordinates of the bounding box.
        
        Returns:
            Dictionary mapping entity IDs to their positions within the bounding box.
        
        Raises:
            ValueError: If min_coords > max_coords or DML is not available.
        """
        if not self._dml:
            raise ValueError("CoordinateSystemDML instance required for spatial queries")
        return self._dml.list_entities_in_bounding_box(min_coords, max_coords)

    def find_nearest_entity(self, type_prefix: Optional[str] = None) -> Optional[Tuple[EntityID, Coordinate3D]]:
        """
        Find the nearest entity to this entity's position, optionally filtered by type prefix.
        
        Args:
            type_prefix: Optional prefix to filter entities (e.g., 'player', 'npc').
        
        Returns:
            Tuple of (entity_id, position) for the nearest entity, or None if none found.
        
        Raises:
            ValueError: If DML is not available.
        """
        if not self._dml:
            raise ValueError("CoordinateSystemDML instance required for spatial queries")
        current_pos = self.position
        if not current_pos:
            return None
        return self._dml.find_nearest_entity(current_pos, type_prefix)

    def is_near_geometry(self, category: str, max_distance: float) -> bool:
        """
        Check if the entity is within max_distance of geometry in the specified category.
        
        Args:
            category: Geometry category (e.g., 'ground_plane', 'wall').
            max_distance: Maximum distance to consider.
        
        Returns:
            True if the entity is near the specified geometry, False otherwise.
        
        Raises:
            KeyError: If the entity is not found in the database.
            ValueError: If DML is not available.
        """
        if not self._dml:
            raise ValueError("CoordinateSystemDML instance required for spatial queries")
        return self._dml.is_entity_near_geometry(self._entity_id, category, max_distance)

    def save_state(self) -> None:
        """
        Save the current state of the coordinate system to the database.
        
        Raises:
            ValueError: If persistence is not available.
        """
        if not self._persistence:
            raise ValueError("CoordinateSystemPersistence instance required for saving state")
        self._persistence.save_coordinate_system(self._coordinate_system)

    @abstractmethod
    def update(self) -> None:
        """
        Abstract method for updating entity-specific state or behavior.
        Subclasses must implement this to define custom update logic.
        """
        pass

    def __str__(self) -> str:
        """String representation of the entity."""
        pos = self.position or "unknown"
        return f"Entity(id={self._entity_id}, position={pos})"