import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from PIL import ImageFont


class Config:
    """Handles configuration loading and validation for the photo frame application."""
    
    # Default configuration values
    DEFAULTS = {
        'photos_directory': str(Path.home() / 'Pictures'),
        'display_time': '10s',
        'transition_time': '1s',
        'random_order': True,
        'blur_zoom_background': False,
        'show_metadata': True,
        'metadata_opacity': 70,
        'metadata_font': 'segoeui.ttf',
        'metadata_point_size': 20,
        # Clock overlay settings
        'show_clock': True,
        'clock_position': 'top-center',
        'clock_opacity': 30,
        'clock_font': 'segoeui.ttf',
        'clock_point_size': 12,
        'clock_format': 'HH:mm'
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration.
        
        Args:
            config_path: Path to the YAML configuration file. If None, uses default values.
        """
        self._config = self.DEFAULTS.copy()
        self.config_path = config_path
        
        if config_path and os.path.exists(config_path):
            self.load()
    
    def load(self, config_path: Optional[str] = None) -> None:
        """Load configuration from a YAML file.
        
        Args:
            config_path: Path to the YAML configuration file. Uses instance path if None.
        """
        if config_path:
            self.config_path = config_path
            
        if not self.config_path or not os.path.exists(self.config_path):
            return
            
        try:
            with open(self.config_path, 'r') as f:
                user_config = yaml.safe_load(f) or {}
                # Allow all configuration settings from the file, not just ones in DEFAULTS
                self._config.update(user_config)
        except Exception as e:
            print(f"Error loading config file: {e}. Using default settings.")
    
    def save(self, config_path: Optional[str] = None) -> None:
        """Save current configuration to a YAML file.
        
        Args:
            config_path: Path to save the configuration. Uses instance path if None.
        """
        if config_path:
            self.config_path = config_path
            
        if not self.config_path:
            return
            
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key to retrieve.
            default: Default value if key doesn't exist.
            
        Returns:
            The configuration value or default if not found.
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key to set.
            value: Value to set.
        """
        if key in self.DEFAULTS:
            self._config[key] = value
    
    def parse_display_time(self, time_str: str) -> int:
        """Parse a time string with units into milliseconds.
        
        Args:
            time_str: Time string with optional unit (s=seconds, m=minutes, h=hours, d=days).
            
        Returns:
            Time in milliseconds.
        """
        time_str = time_str.lower().strip()
        if time_str.endswith('s'):
            return int(float(time_str[:-1]) * 1000)
        elif time_str.endswith('m'):
            return int(float(time_str[:-1]) * 60 * 1000)
        elif time_str.endswith('h'):
            return int(float(time_str[:-1]) * 60 * 60 * 1000)
        elif time_str.endswith('d'):
            return int(float(time_str[:-1]) * 24 * 60 * 60 * 1000)
        return int(float(time_str) * 1000)  # Default to seconds if no unit
    
    def get_display_time_ms(self) -> int:
        """Get the display time in milliseconds."""
        return self.parse_display_time(self._config['display_time'])
        
    def get_transition_time_ms(self) -> int:
        """Get the transition time in milliseconds."""
        # Handle both string format (e.g. "1s") and numeric format (backward compatibility)
        transition_time = self._config['transition_time']
        return self.parse_display_time(transition_time)
    
    def check_font(self) -> ImageFont:
        try:
            return ImageFont.truetype(self._config['metadata_font'], self._config['metadata_point_size'])
        except Exception as e:
            print(f"Error loading font: {e}")
            return ImageFont.load_default()

    def to_dict(self) -> Dict[str, Any]:
        """Get the current configuration as a dictionary."""
        return self._config.copy()
    
    def update(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            new_config: Dictionary of new configuration values.
        """
        for key, value in new_config.items():
            if key in self._config:
                self._config[key] = value
