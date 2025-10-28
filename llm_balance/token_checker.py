"""
Main token checker functionality
"""

import json
from typing import List, Dict, Any, Optional
from .config import ConfigManager
from .platform_configs import PlatformConfig
from .platform_handlers.base import BasePlatformHandler, PlatformTokenInfo
from .token_formatter import format_model_tokens
from .platform_handlers import create_handler

class TokenChecker:
    """Main token checker class"""
    
    def __init__(self, config_file: str = None, browser: str = None):
        self.config_manager = ConfigManager(config_file)
        # Use provided browser or fall back to global configuration
        self.browser = browser or self.config_manager.get_global_browser()
        self.handlers = {}
    
    def check_all_tokens(self) -> List[Dict[str, Any]]:
        """Check token balances for all enabled platforms"""
        tokens = []

        for platform_config in self.config_manager.get_enabled_platforms():
            try:
                # Skip platforms with show_package disabled
                if not platform_config.show_package:
                    continue

                handler = self._get_handler(platform_config)
                try:
                    token_info = handler.get_model_tokens()
                    # Convert PlatformTokenInfo to dict format for backward compatibility
                    platform_data = {
                        'platform': token_info.platform,
                        'models': [
                            {
                                'model': model.model,
                                'package': model.package,
                                'remaining_tokens': model.remaining_tokens,
                                'used_tokens': model.used_tokens,
                                'total_tokens': model.total_tokens,
                                'status': model.status
                            }
                            for model in token_info.models
                        ],
                        'raw_data': token_info.raw_data
                    }
                    tokens.append(platform_data)
                except NotImplementedError:
                    # Platform doesn't support token checking - skip it
                    continue
            except Exception as e:
                # Skip platforms that don't support tokens or have errors
                continue

        return tokens
    
    def check_platform_tokens(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Check token balance for a specific platform"""
        platform_config = self.config_manager.get_platform(platform_name)
        if not platform_config:
            print(f"Platform {platform_name} not found in configuration")
            return None

        # Check if package display is disabled
        if hasattr(platform_config, 'show_package') and not platform_config.show_package:
            print(f"Package display is disabled for platform {platform_name}")
            return None

        try:
            # platform_config is already a PlatformConfig object

            handler = self._get_handler(platform_config)
            try:
                token_info = handler.get_model_tokens()
                # Convert PlatformTokenInfo to dict format for backward compatibility
                # Filter out non-serializable objects from raw_data
                filtered_raw_data = self._clean_raw_data_for_json(token_info.raw_data)

                return {
                    'platform': token_info.platform,
                    'models': [
                        {
                            'model': model.model,
                            'package': model.package,
                            'remaining_tokens': model.remaining_tokens,
                            'used_tokens': model.used_tokens,
                            'total_tokens': model.total_tokens,
                            'status': model.status
                        }
                        for model in token_info.models
                    ],
                    'raw_data': filtered_raw_data
                }
            except NotImplementedError:
                # Platform doesn't support token checking
                return None
        except Exception as e:
            # Skip platforms that don't support tokens or have errors
            return None
    
    def _clean_raw_data_for_json(self, raw_data):
        """Clean raw data to make it JSON serializable"""
        if not raw_data:
            return {}
        
        def clean_value(value):
            """Recursively clean values"""
            if isinstance(value, dict):
                return {k: clean_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [clean_value(item) for item in value]
            elif hasattr(value, '__dict__'):
                # Convert object to dict, skipping Configuration objects
                obj_name = value.__class__.__name__
                if obj_name == 'Configuration':
                    return f"<{obj_name} object>"
                return {k: clean_value(v) for k, v in value.__dict__.items()}
            else:
                try:
                    # Test if the value is JSON serializable
                    json.dumps(value)
                    return value
                except (TypeError, ValueError):
                    return f"<{value.__class__.__name__} object>"
        
        return clean_value(raw_data)
    
    def _get_handler(self, config: PlatformConfig) -> BasePlatformHandler:
        """Get handler instance for platform configuration"""
        if config.name not in self.handlers:
            self.handlers[config.name] = create_handler(config, self.browser)
        return self.handlers[config.name]
    
    def list_platforms(self) -> List[str]:
        """List all available platforms"""
        return self.config_manager.list_platforms()
    
    def list_enabled_platforms(self) -> List[str]:
        """List enabled platforms"""
        return [cfg.name for cfg in self.config_manager.get_enabled_platforms()]
    
    def format_tokens(
        self,
        tokens: List[Dict[str, Any]],
        format_type: str = 'table',
        target_currency: str = 'CNY',
        model: Optional[str] = None,
        show_all: bool = False,
    ) -> str:
        """Format token information in specified format"""
        return format_model_tokens(tokens, format_type, target_currency, model, show_all)
