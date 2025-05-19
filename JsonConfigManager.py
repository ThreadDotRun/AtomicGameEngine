import json
import os
from typing import Dict, List, Optional

class JsonConfigManager:
    def __init__(self, config_path: str) -> None:
        """Initialize with path to JSON config file.
        
        Args:
            config_path (str): Path to the JSON file (e.g., 'terrain_config.json').
        
        Raises:
            FileNotFoundError: If the config file does not exist.
            ValueError: If the config file is not a valid JSON file.
        """
        self.config_path = config_path
        self.config_data: Dict = {}
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        if not config_path.endswith('.json'):
            raise ValueError(f"Configuration file must be a JSON file: {config_path}")
        
        # Load config during initialization
        self.load_config()

    def load_config(self) -> Dict:
        """Load and return JSON data as a dictionary.
        
        Returns:
            Dict: The parsed JSON configuration data.
        
        Raises:
            json.JSONDecodeError: If the JSON file is malformed.
            IOError: If there is an error reading the file.
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config_data = json.load(file)
            return self.config_data
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Malformed JSON in {self.config_path}: {str(e)}", e.doc, e.pos)
        except IOError as e:
            raise IOError(f"Error reading {self.config_path}: {str(e)}")

    def validate_config(self, schema: Dict) -> bool:
        """Validate JSON against a schema (e.g., move_cost > 0).
        
        Args:
            schema (Dict): Schema defining validation rules for each key.
                           Example: {
                               'desert': {
                                   'move_cost': {'type': 'int', 'min': 1},
                                   'weight': {'type': 'float', 'min': 0, 'max': 1},
                                   'color': {'type': 'list', 'length': 3}
                               }
                           }
        
        Returns:
            bool: True if validation passes, False otherwise.
        
        Raises:
            ValueError: If validation fails, with details of the error.
        """
        if not self.config_data:
            raise ValueError("No configuration data loaded. Call load_config() first.")

        for config_key, config_values in self.config_data.items():
            if config_key not in schema:
                continue  # Skip keys not in schema
                
            schema_rules = schema.get(config_key, {})
            
            for field, rules in schema_rules.items():
                if field not in config_values:
                    raise ValueError(f"Missing field '{field}' in config key '{config_key}'")
                
                value = config_values[field]
                field_type = rules.get('type')
                
                # Type checking
                if field_type == 'int' and not isinstance(value, int):
                    raise ValueError(f"Field '{field}' in '{config_key}' must be an integer")
                elif field_type == 'float' and not isinstance(value, (int, float)):
                    raise ValueError(f"Field '{field}' in '{config_key}' must be a float")
                elif field_type == 'list' and not isinstance(value, list):
                    raise ValueError(f"Field '{field}' in '{config_key}' must be a list")
                
                # Range checking
                if 'min' in rules and value < rules['min']:
                    raise ValueError(f"Field '{field}' in '{config_key}' must be >= {rules['min']}")
                if 'max' in rules and value > rules['max']:
                    raise ValueError(f"Field '{field}' in '{config_key}' must be <= {rules['max']}")
                
                # Length checking for lists
                if field_type == 'list' and 'length' in rules and len(value) != rules['length']:
                    raise ValueError(f"Field '{field}' in '{config_key}' must have length {rules['length']}")
        
        return True

    def get_config(self, key: str) -> Dict:
        """Retrieve config data for a specific key (e.g., 'desert').
        
        Args:
            key (str): The configuration key to retrieve (e.g., 'desert').
        
        Returns:
            Dict: The configuration data for the key.
        
        Raises:
            KeyError: If the key does not exist in the config data.
        """
        if not self.config_data:
            raise ValueError("No configuration data loaded. Call load_config() first.")
        
        if key not in self.config_data:
            raise KeyError(f"Configuration key '{key}' not found in {self.config_path}")
        
        return self.config_data[key]

    def get_all_keys(self) -> List[str]:
        """Return list of all top-level keys (e.g., ['desert', 'swamp']).
        
        Returns:
            List[str]: List of top-level configuration keys.
        
        Raises:
            ValueError: If no configuration data is loaded.
        """
        if not self.config_data:
            raise ValueError("No configuration data loaded. Call load_config() first.")
        
        return list(self.config_data.keys())