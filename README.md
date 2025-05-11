# Coordinate System Components README
This README provides a compact yet comprehensive overview of three Python components for managing 3D spatial data: CoordinateSystem, CoordinateSystemPersistence, and CoordinateSystemDML. These components form an atomic system for storing, persisting, and querying coordinates for entities (e.g., players, NPCs) and static geometry (e.g., walls, planes) in games or data analysis applications.

## Overview
- **CoordinateSystem**: Manages in-memory 3D coordinates for dynamic entities and static geometry (planes, polygons). Provides basic CRUD operations.
- **CoordinateSystemPersistence**: Persists CoordinateSystem data to a SQLite database and retrieves it, enabling durable storage.
- **CoordinateSystemDML**: Executes SQL queries on a SQLite database created by CoordinateSystemPersistence, supporting spatial analysis without an in-memory CoordinateSystem.

## Dependencies
- **Python standard library**: sqlite3, json, math, os.
- **Type aliases**:
  - `Coordinate3D`: Tuple[float, float, float] (e.g., (x, y, z)).
  - `EntityID`: Union[str, int] (e.g., "player_1", 42).
  - `GeometryID`: str (e.g., "wall1").

## Component APIs

### CoordinateSystem
**Description**: Stores and manages 3D coordinates for entities and static geometry in memory. Supports adding, updating, removing, and querying positions.

**API**
- `__init__(self) -> None`: Initializes empty storage for entities and geometry.
- `get_version(self) -> str`: Returns version string from version.txt or "unknown version".
- `get_info_message(self) -> str`: Returns info from info.txt or default message.
- `add_entity(self, entity_id: EntityID, position: Coordinate3D) -> None`: Adds or updates an entity’s position. Raises TypeError for invalid coordinates.
- `remove_entity(self, entity_id: EntityID) -> None`: Removes an entity. Raises KeyError if not found.
- `update_entity_position(self, entity_id: EntityID, new_position: Coordinate3D) -> None`: Updates an entity’s position. Raises KeyError or TypeError.
- `get_entity_position(self, entity_id: EntityID) -> Optional[Coordinate3D]`: Returns entity’s position or None.
- `get_all_entity_positions(self) -> Dict[EntityID, Coordinate3D]`: Returns all entity positions.
- `add_static_plane(self, geometry_id: GeometryID, origin: Coordinate3D, normal: Coordinate3D, category: str = "generic_plane") -> None`: Adds a plane. Raises ValueError for duplicate ID, TypeError for invalid inputs.
- `add_static_polygon(self, geometry_id: GeometryID, vertices: List[Coordinate3D], category: str = "generic_polygon") -> None`: Adds a polygon (3+ vertices). Raises ValueError or TypeError.
- `get_static_geometry(self, geometry_id: GeometryID) -> Optional[Dict[str, Any]]`: Returns geometry definition or None. Planes: `{"type": "plane", "origin": Coordinate3D, "normal": Coordinate3D, "category": str}`; Polygons: `{"type": "polygon", "vertices": List[Coordinate3D], "category": str}`.
- `remove_static_geometry(self, geometry_id: GeometryID) -> None`: Removes geometry. Raises KeyError.
- `list_static_geometry_by_category(self, category: str) -> Dict[GeometryID, Dict[str, Any]]`: Returns geometries by category.
- `list_all_static_geometry(self) -> Dict[GeometryID, Dict[str, Any]]`: Returns all geometries.

**Usage Example**
```python
from CoordinateSystem import CoordinateSystem

cs = CoordinateSystem()
cs.add_entity("player_1", (1.0, 0.0, 0.0))
cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), "ground_plane")
print(cs.get_entity_position("player_1"))  # (1.0, 0.0, 0.0)
print(cs.list_static_geometry_by_category("ground_plane"))  # {"ground": {...}}
print(cs.get_version())  # e.g., "0.1.0" or "unknown version"
```

### CoordinateSystemPersistence
**Description**: Persists CoordinateSystem data to a SQLite database and retrieves it. Uses a named database file for storage.

**API**
- `__init__(self, db_name: str) -> None`: Initializes connection to db_name.db, creating tables (entities, geometry, metadata) if needed.
- `save_coordinate_system(self, cs: CoordinateSystem) -> None`: Saves all entities and geometry to the database, overwriting existing data. Updates last_saved_at metadata.
- `load_coordinate_system(self) -> CoordinateSystem`: Returns a new CoordinateSystem populated with database data.
- `get_database_info(self) -> Dict[str, Any]`: Returns `{"db_name": str, "created_at": str|None, "last_saved_at": str|None, "entity_count": int, "geometry_count": int}`.

**Usage Example**
```python
from CoordinateSystem import CoordinateSystem
from CoordinateSystemPersistence import CoordinateSystemPersistence

cs = CoordinateSystem()
cs.add_entity("player_1", (1.0, 0.0, 0.0))
cs.add_static_plane("ground", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0))

persistence = CoordinateSystemPersistence("game_state")
persistence.save_coordinate_system(cs)
print(persistence.get_database_info())  # {"db_name": "game_state", "entity_count": 1, ...}

loaded_cs = persistence.load_coordinate_system()
print(loaded_cs.get_entity_position("player_1"))  # (1.0, 0.0, 0.0)
```

### CoordinateSystemDML
**Description**: Executes SQL queries on a SQLite database created by CoordinateSystemPersistence, providing spatial analysis (e.g., proximity, bounding box queries). Maintains a single connection per instance.

**API**
- `__init__(self, db_name: str) -> None`: Connects to db_name.db. Raises FileNotFoundError if missing.
- `count_entities(self, type_prefix: Optional[str] = None) -> Union[int, Dict[str, int]]`: Returns total entity count or counts by type prefix (e.g., `{"player": 1}`).
- `list_entities_in_bounding_box(self, min_coords: Coordinate3D, max_coords: Coordinate3D) -> Dict[EntityID, Coordinate3D]`: Returns entities within the box. Raises ValueError if min_coords exceeds max_coords.
- `find_nearest_entity(self, point: Coordinate3D, type_prefix: Optional[str] = None) -> Optional[Tuple[EntityID, Coordinate3D]]`: Returns closest entity or None.
- `list_geometry_by_category(self, category: str) -> Dict[GeometryID, Dict[str, Any]]`: Returns geometries by category (planes: origin, normal; polygons: vertices).
- `is_entity_near_geometry(self, entity_id: EntityID, category: str, max_distance: float) -> bool`: Returns True if entity is within max_distance of geometry (vertex-based for polygons). Raises KeyError if entity not found.

**Usage Example**
```python
from CoordinateSystemDML import CoordinateSystemDML

dml = CoordinateSystemDML("game_state")
print(dml.count_entities())  # 1
print(dml.list_entities_in_bounding_box((0.0, 0.0, 0.0), (1.5, 1.5, 1.5)))  # {"player_1": (1.0, 0.0, 0.0)}
print(dml.find_nearest_entity((1.0, 0.0, 0.0), "player"))  # ("player_1", (1.0, 0.0, 0.0))
print(dml.list_geometry_by_category("ground_plane"))  # {"ground": {"type": "plane", ...}}
print(dml.is_entity_near_geometry("player_1", "ground_plane", 1.0))  # True
```

## Notes
- **Performance**: SQLite on SSD supports 64 entities at 0.1s updates (12-53 ms), improved on RAM drive (~4-11 ms). Optimize with synchronous=0, WAL mode, or selective updates for larger scales.
- **Conventions**: EntityIDs may include type prefixes (e.g., "player_1") for filtering. Geometry categories (e.g., "wall") are user-defined.
- **Database**: CoordinateSystemPersistence and CoordinateSystemDML use db_name.db files. Ensure compatibility in schema.
- **Error Handling**: Methods raise TypeError, ValueError, KeyError, or FileNotFoundError for invalid inputs or missing data.
- **Files**: Classes are in CoordinateSystem.py, CoordinateSystemPersistence.py, and CoordinateSystemDML.py.

This system is lightweight, extensible, and suitable for real-time applications with proper optimization.