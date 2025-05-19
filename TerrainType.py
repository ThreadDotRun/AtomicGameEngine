from JsonConfigManager import JsonConfigManager

class TerrainType:
    @staticmethod
    def load_config(config_path: str) -> dict:
        """Loads terrain configuration using JsonConfigManager.
        
        Args:
            config_path (str): Path to terrain_config.json.
        
        Returns:
            dict: Terrain configuration data with 5 types (desert, swamp, forest, mountain, plains).
        
        Raises:
            FileNotFoundError: If config_path does not exist.
            ValueError: If JSON is invalid or fails validation.
        """
        config_manager = JsonConfigManager(config_path)
        
        schema = {
            key: {
                "move_cost": {"type": "int", "min": 1},
                "weight": {"type": "float", "min": 0, "max": 1},
                "color": {"type": "list", "length": 3},
                "sprite": {
                    "background": {"color": {"type": "list", "length": 3}},
                    "shapes": {"type": "list"}
                }
            } for key in ["desert", "swamp", "forest", "mountain", "plains"]
        }
        
        if not config_manager.validate_config(schema):
            raise ValueError(f"Invalid terrain configuration in {config_path}")
        
        return config_manager.load_config()

    @staticmethod
    def init_sprites() -> None:
        """Initializes terrain sprites for rendering."""
        pass