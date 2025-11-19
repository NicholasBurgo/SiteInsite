import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigLoader:
    """Load and validate scraper configuration from YAML"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or Path(__file__).parent / "config.yaml"
        self._config: Optional[Dict[str, Any]] = None

    def load(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if self._config is not None:
            return self._config

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)

        self._validate_config()
        return self._config

    def _validate_config(self):
        """Validate configuration structure"""
        required_sections = ['scraper']
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required config section: {section}")

        scraper_config = self._config['scraper']

        # Validate proxy settings
        if scraper_config.get('proxies', {}).get('enabled', False):
            proxies = scraper_config['proxies']
            if 'residential' not in proxies:
                raise ValueError("Residential proxies must be configured when proxies are enabled")

        # Validate targets
        if 'targets' not in scraper_config:
            raise ValueError("At least one target site must be configured")

    def get(self, key: str, default=None):
        """Get configuration value by dot-separated key"""
        config = self.load()
        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_target_config(self, site_name: str) -> Dict[str, Any]:
        """Get configuration for specific target site"""
        targets = self.get('scraper.targets', {})
        if site_name not in targets:
            raise ValueError(f"Target site '{site_name}' not configured")
        return targets[site_name]

# Global config instance
config_loader = ConfigLoader()
