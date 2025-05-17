from typing import Tuple, Dict, Optional, List, Any

Coordinate3D = Tuple[float, float, float]
EntityID = str
GeometryID = str

class CoordinateSystem:
    def __init__(self):
        self._entity_positions: Dict[EntityID, Coordinate3D] = {}
        self._static_geometry: Dict[GeometryID, Dict[str, Any]] = {}

    def add_entity(self, entity_id: EntityID, position: Coordinate3D) -> None:
        if not (isinstance(position, tuple) and len(position) == 3 and
                all(isinstance(coord, (int, float)) for coord in position)):
            raise TypeError("Position must be a tuple of three numbers (x, y, z).")
        self._entity_positions[entity_id] = tuple(float(c) for c in position)

    def remove_entity(self, entity_id: EntityID) -> None:
        if entity_id not in self._entity_positions:
            raise KeyError(f"Entity with ID '{entity_id}' not found.")
        del self._entity_positions[entity_id]

    def update_entity_position(self, entity_id: EntityID, new_position: Coordinate3D) -> None:
        if entity_id not in self._entity_positions:
            raise KeyError(f"Entity with ID '{entity_id}' not found for update.")
        if not (isinstance(new_position, tuple) and len(new_position) == 3 and
                all(isinstance(coord, (int, float)) for coord in new_position)):
            raise TypeError("New position must be a tuple of three numbers (x, y, z).")
        self._entity_positions[entity_id] = tuple(float(c) for c in new_position)  # Fixed to use new_position

    def get_entity_position(self, entity_id: EntityID) -> Optional[Coordinate3D]:
        return self._entity_positions.get(entity_id)

    def get_all_entity_positions(self) -> Dict[EntityID, Coordinate3D]:
        return self._entity_positions.copy()

    def add_static_polygon(self, geometry_id: GeometryID, vertices: List[Coordinate3D], category: str = "generic_polygon") -> None:
        if geometry_id in self._static_geometry:
            raise ValueError(f"Static geometry with ID '{geometry_id}' already exists.")
        if not isinstance(vertices, list) or len(vertices) < 3:
            raise ValueError("Vertices must be a list of at least 3 coordinate tuples.")
        if not all(isinstance(v, tuple) and len(v) == 3 and
                   all(isinstance(c, (int, float)) for c in v) for v in vertices):
            raise TypeError("Each vertex must be a tuple of three numbers (x, y, z).")
        self._static_geometry[geometry_id] = {
            "type": "polygon",
            "vertices": [tuple(float(c) for c in v) for v in vertices],
            "category": category
        }

    def get_static_geometry(self, geometry_id: GeometryID) -> Optional[Dict[str, Any]]:
        return self._static_geometry.get(geometry_id)

    def list_static_geometry_by_category(self, category: str) -> Dict[GeometryID, Dict[str, Any]]:
        return {gid: gdef for gid, gdef in self._static_geometry.items() if gdef.get("category") == category}

    def list_all_static_geometry(self) -> Dict[GeometryID, Dict[str, Any]]:
        return self._static_geometry.copy()