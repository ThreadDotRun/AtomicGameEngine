# Atomic Coordinate System Engine README

📢❗🚨 **Note**: This engine features an embedded SQLite database for persistence and querying of spatial coordinates, integrated with an abstract `Entity` class for flexible entity management. See performance notes at the bottom for hardware optimization suggestions.

This README provides an overview of the **Atomic Coordinate System Engine**, a Python-based framework for managing 3D spatial data in real-time applications such as games or simulations. The engine leverages a unique coordinate system backed by SQLite for persistence and querying, making it ideal for applications requiring durable storage and spatial analysis. Included in this project is a hex-based demo game (`gamedemo.py`) that showcases the engine's capabilities through a hexagonal grid map with terrain, units, cities, and pathfinding.

## Overview

The **Atomic Coordinate System Engine** consists of four core components for managing 3D spatial data:

- **`CoordinateSystem`**: Manages in-memory 3D coordinates for dynamic entities (e.g., units) and static geometry (e.g., terrain polygons). Provides basic CRUD operations.
- **`CoordinateSystemPersistence`**: Persists `CoordinateSystem` data to a SQLite database, enabling durable storage and retrieval of spatial data.
- **`CoordinateSystemDML`**: Executes SQL queries on the SQLite database, supporting spatial analysis such as bounding box queries and proximity checks.
- **`Entity`**: An abstract base class for entities, providing a unified interface to manage positions, perform spatial queries, and persist data using the other components.

### Demonstration: Hex-Based Game

To demonstrate the engine's capabilities, this project includes a hex-based game demo (`gamedemo.py`). The demo features:

- A procedurally generated hexagonal grid map (`HexMap.py`) with varied terrain types (ocean, plain, hill, mountain, stream).
- Entities like units (`Unit.py`) and cities (`City.py`) that move and interact on the map.
- Pathfinding (`Pathfinding.py`) using A* to navigate the hex grid, accounting for terrain movement costs.
- Visual rendering (`HexUtils.py`) with hexagonal masking to ensure terrain sprites are clipped to their hex boundaries.
- Resource placement (`ResourceType.py`) on the map for added gameplay depth.

The demo leverages the engine's SQLite-backed coordinate system to store and query the positions of hex tiles, units, cities, and resources, showcasing the engine's ability to handle complex spatial relationships and persistence in a game setting.

![Hex Game Clone a6](./assets/images/readme_image_1.png)

## Dependencies

- **Python Standard Library**: `sqlite3`, `json`, `math`, `os`, `abc`, `random`, `typing`.
- **External Packages**: `pygame` (for the demo game rendering).
- **Type Aliases**:
  - `Coordinate3D`: `Tuple[float, float, float]` (e.g., `(x, y, z)`).
  - `EntityID`: `str` (e.g., `"unit_0"`).
  - `GeometryID`: `str` (e.g., `"hex_0_0"`).

## Component APIs

### CoordinateSystem

**Description**: Manages in-memory 3D coordinates for entities and static geometry. Supports adding, updating, removing, and querying positions.

**API**:

- `__init__(self) -> None`: Initializes empty storage for entities and geometry.
- `add_entity(self, entity_id: EntityID, position: Coordinate3D) -> None`: Adds or updates an entity’s position. Raises `TypeError` for invalid coordinates.
- `remove_entity(self, entity_id: EntityID) -> None`: Removes an entity. Raises `KeyError` if not found.
- `update_entity_position(self, entity_id: EntityID, new_position: Coordinate3D) -> None`: Updates an entity’s position. Raises `KeyError` or `TypeError`.
- `get_entity_position(self, entity_id: EntityID) -> Optional[Coordinate3D]`: Returns the entity’s position or `None`.
- `get_all_entity_positions(self) -> Dict[EntityID, Coordinate3D]`: Returns all entity positions.
- `add_static_polygon(self, geometry_id: GeometryID, vertices: List[Coordinate3D], category: str = "generic_polygon") -> None`: Adds a polygon (3+ vertices). Raises `ValueError` or `TypeError`.
- `get_static_geometry(self, geometry_id: GeometryID) -> Optional[Dict[str, Any]]`: Returns geometry definition or `None`. Polygons: `{"type": "polygon", "vertices": List[Coordinate3D], "category": str}`.
- `list_static_geometry_by_category(self, category: str) -> Dict[GeometryID, Dict[str, Any]]`: Returns geometries by category.
- `list_all_static_geometry(self) -> Dict[GeometryID, Dict[str, Any]]`: Returns all geometries.

**Usage Example**:

```python
from CoordinateSystem import CoordinateSystem

cs = CoordinateSystem()
cs.add_entity("unit_0", (1.0, 0.0, 0.0))
cs.add_static_polygon("hex_0_0", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)], "plain")
print(cs.get_entity_position("unit_0"))  # (1.0, 0.0, 0.0)
print(cs.list_static_geometry_by_category("plain"))  # {"hex_0_0": {...}}
```

### CoordinateSystemPersistence

**Description**: Persists `CoordinateSystem` data to a SQLite database, enabling durable storage and retrieval.

**API**:

- `__init__(self, db_name: str) -> None`: Initializes connection to `db_name.db`, creating tables (`entities`, `geometry`) if needed.
- `save_coordinate_system(self, cs: CoordinateSystem) -> None`: Saves all entities and geometry to the database, overwriting existing data.
- `load_coordinate_system(self) -> CoordinateSystem`: Returns a new `CoordinateSystem` populated with database data.

**Usage Example**:

```python
from CoordinateSystem import CoordinateSystem
from CoordinateSystemPersistence import CoordinateSystemPersistence

cs = CoordinateSystem()
cs.add_entity("unit_0", (1.0, 0.0, 0.0))

persistence = CoordinateSystemPersistence("game_state")
persistence.save_coordinate_system(cs)

loaded_cs = persistence.load_coordinate_system()
print(loaded_cs.get_entity_position("unit_0"))  # (1.0, 0.0, 0.0)
```

### CoordinateSystemDML

**Description**: Executes SQL queries on a SQLite database created by `CoordinateSystemPersistence`, providing spatial analysis (e.g., proximity, bounding box queries).

**API**:

- `__init__(self, conn: sqlite3.Connection) -> None`: Initializes with a SQLite connection.
- `count_entities(self, type_prefix: Optional[str] = None) -> Union[int, Dict[str, int]]`: Returns total entity count or counts by type prefix (e.g., `{"unit": 1}`).
- `list_entities_in_bounding_box(self, min_coords: Coordinate3D, max_coords: Coordinate3D) -> Dict[EntityID, Coordinate3D]`: Returns entities within the box. Raises `ValueError` if `min_coords` exceeds `max_coords`.
- `find_nearest_entity(self, point: Coordinate3D, type_prefix: Optional[str] = None) -> Optional[Tuple[EntityID, Coordinate3D]]`: Returns the closest entity or `None`.
- `list_geometry_by_category(self, category: str) -> Dict[GeometryID, Dict[str, Any]]`: Returns geometries by category.
- `is_entity_near_geometry(self, entity_id: EntityID, category: str, max_distance: float) -> bool`: Returns `True` if the entity is within `max_distance` of geometry. Raises `KeyError` if the entity is not found.

**Usage Example**:

```python
from CoordinateSystemDML import CoordinateSystemDML
from CoordinateSystemPersistence import CoordinateSystemPersistence

persistence = CoordinateSystemPersistence("game_state")
dml = CoordinateSystemDML(persistence.conn)
print(dml.count_entities())  # 1
print(dml.list_entities_in_bounding_box((0.0, 0.0, 0.0), (1.5, 1.5, 1.5)))  # {"unit_0": (1.0, 0.0, 0.0)}
print(dml.find_nearest_entity((1.0, 0.0, 0.0), "unit"))  # ("unit_0", (1.0, 0.0, 0.0))
```

### Entity

**Description**: Abstract base class for entities (e.g., units, cities) in the 3D coordinate system. Integrates with `CoordinateSystem`, `CoordinateSystemDML`, and `CoordinateSystemPersistence`.

**API**:

- `__init__(self, entity_id: EntityID, position: Coordinate3D, coordinate_system: CoordinateSystem, dml: Optional[CoordinateSystemDML] = None, persistence: Optional[CoordinateSystemPersistence] = None) -> None`: Initializes an entity. Raises `ValueError` for invalid inputs.
- `entity_id(self) -> EntityID` (property): Returns the entity’s unique ID.
- `position(self) -> Optional[Coordinate3D]` (property): Returns the entity’s current position or `None`.
- `update_position(self, new_position: Coordinate3D) -> None`: Updates the entity’s position and persists if persistence is available. Raises `KeyError` or `TypeError`.
- `remove(self) -> None`: Removes the entity from the coordinate system and persists. Raises `KeyError`.
- `get_nearby_entities(self, min_coords: Coordinate3D, max_coords: Coordinate3D) -> Dict[EntityID, Coordinate3D]`: Returns entities within a bounding box via DML. Raises `ValueError` if DML is unavailable.
- `find_nearest_entity(self, type_prefix: Optional[str] = None) -> Optional[Tuple[EntityID, Coordinate3D]]`: Returns the nearest entity via DML. Raises `ValueError` if DML is unavailable.
- `is_near_geometry(self, category: str, max_distance: float) -> bool`: Returns `True` if the entity is near specified geometry via DML. Raises `ValueError` or `KeyError`.
- `save_state(self) -> None`: Saves the coordinate system state via persistence. Raises `ValueError` if persistence is unavailable.
- `update(self) -> None` (abstract): Subclasses must implement custom update logic.
- `__str__(self) -> str`: Returns a string representation, e.g., `Entity(id=unit_0, position=(1.0, 0.0, 0.0))`.

**Usage Example**:

```python
from CoordinateSystem import CoordinateSystem
from CoordinateSystemDML import CoordinateSystemDML
from CoordinateSystemPersistence import CoordinateSystemPersistence
from Entity import Entity

class Unit(Entity):
    def update(self):
        if self.position:
            new_pos = (self.position[0] + 0.1, self.position[1], self.position[2])
            self.update_position(new_pos)

cs = CoordinateSystem()
persistence = CoordinateSystemPersistence("game_db")
dml = CoordinateSystemDML(persistence.conn)

unit = Unit("unit_0", (1.0, 0.0, 0.0), cs, dml, persistence)
unit.update()
print(unit.position)  # (1.1, 0.0, 0.0)
unit.save_state()
```

## Demo Game Features

The hex-based demo game (`gamedemo.py`) demonstrates the engine's capabilities:

- **Hexagonal Grid**: Generated using `HexMap.py`, with terrain rules ensuring natural-looking maps (e.g., oceans near streams, mountains near hills).
- **Rendering**: `HexUtils.py` renders hex tiles with terrain sprites, using hexagonal masking to prevent sprite overlap.
- **Entities**: Units and cities are managed as entities, with positions stored and queried via the engine.
- **Pathfinding**: `Pathfinding.py` implements A* pathfinding on the hex grid, using terrain movement costs stored in `TerrainType.py`.
- **Persistence**: The game state (hex tiles, units, cities, resources) is persisted to SQLite, allowing the map to be saved and loaded.
- **Interactivity**: Players can select units, move them across the map, zoom in/out, pan the camera, and advance turns.

## Notes

- **Performance**: SQLite on SSD supports 64 entities at 0.1s updates (12-53 ms), improved on RAM drive (~4-11 ms). Optimize with `synchronous=0`, WAL mode, or selective updates for larger scales.
- **Conventions**: Entity IDs often include type prefixes (e.g., `"unit_0"`, `"resource_1_2"`) for filtering. Geometry categories (e.g., `"plain"`, `"wall"`) are user-defined.
- **Database**: `CoordinateSystemPersistence` and `CoordinateSystemDML` use `db_name.db` files with a consistent schema.
- **Error Handling**: Methods raise `TypeError`, `ValueError`, or `KeyError` for invalid inputs or missing data.
- **Files**: Core components are in `CoordinateSystem.py`, `CoordinateSystemPersistence.py`, `CoordinateSystemDML.py`, and `Entity.py`. Demo-related files include `gamedemo.py`, `HexMap.py`, `HexUtils.py`, `Pathfinding.py`, `TerrainType.py`, `ResourceType.py`, `Unit.py`, and `City.py`.
- **Extensibility**: The `Entity` class is abstract, allowing subclasses to define specific behaviors (e.g., movement for units, growth for cities).

This engine is lightweight, extensible, and suitable for real-time applications with proper optimization.