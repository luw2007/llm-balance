"""
Configuration management for LLM platforms
Uses new Python-based configuration system
"""

from typing import Dict, Any, List, Optional
from .platform_configs import ConfigManager as PlatformConfigManager
from .platform_configs import PlatformConfig

class ConfigManager:
    """Manages platform configurations using new Python-based system"""
    
    def __init__(self, config_file: str = None):
        self.platform_config_manager = PlatformConfigManager(config_file)
    
    def get_enabled_platforms(self) -> List[PlatformConfig]:
        """Get list of enabled platforms"""
        return self.platform_config_manager.get_enabled_platforms()
    
    def get_platform(self, name: str) -> Optional[PlatformConfig]:
        """Get platform configuration by name"""
        return self.platform_config_manager.get_platform_config(name)
    
    def update_platform(self, name: str, config: Dict[str, Any]):
        """Update platform configuration"""
        if name not in self.platform_config_manager.user_config:
            self.platform_config_manager.user_config[name] = {}
        self.platform_config_manager.user_config[name].update(config)
        self.platform_config_manager.save_config()
    
    def enable_platform(self, name: str):
        """Enable a platform"""
        self.platform_config_manager.enable_platform(name)
    
    def disable_platform(self, name: str):
        """Disable a platform"""
        self.platform_config_manager.disable_platform(name)
    
    def get_global_browser(self) -> str:
        """Get global browser configuration"""
        return self.platform_config_manager.get_global_config().get('browser', 'chrome')
    
    def set_global_browser(self, browser: str):
        """Set global browser configuration"""
        self.platform_config_manager.set_global_config('browser', browser)
    
    def list_platforms(self) -> List[str]:
        """List all available platforms"""
        return list(self.platform_config_manager.platform_configs.keys())
    
    def get_platform_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get platform information"""
        platform_config = self.platform_config_manager.get_platform_config(name)
        if not platform_config:
            return None
        
        return {
            'name': platform_config.name,
            'display_name': platform_config.display_name,
            'description': platform_config.description,
            'auth_type': platform_config.auth_type,
            'env_var': platform_config.env_var,
            'enabled': platform_config.enabled,
            'config': platform_config.to_dict()
        }
    
    def generate_config_file(self, output_file: str = None) -> str:
        """Generate a complete configuration file"""
        return self.platform_config_manager.generate_config_file(output_file)