"""
Main balance checker functionality
"""

from typing import List, Dict, Any, Optional
import os
from .config import ConfigManager, PlatformConfig
from .platform_handlers.base import BasePlatformHandler, CostInfo
from .utils import get_nested_value, format_output
from .platform_handlers import create_handler
from .error_handler import format_api_key_error, format_auth_error, format_network_error

class BalanceChecker:
    """Main balance checker class"""
    
    def __init__(self, config_file: str = None, browser: str = None):
        self.config_manager = ConfigManager(config_file)
        # Use provided browser or fall back to global config
        self.browser = browser or self.config_manager.global_browser
        self.handlers = {}
    
    def check_all_balances(self) -> List[Dict[str, Any]]:
        """Check balances for all enabled platforms"""
        balances = []
        
        for platform_config in self.config_manager.get_enabled_platforms():
            try:
                handler = self._get_handler(platform_config)
                balance_info = handler.get_balance()
                balances.append({
                    'platform': balance_info.platform,
                    'balance': balance_info.balance,
                    'currency': balance_info.currency,
                    'raw_data': balance_info.raw_data
                })
            except Exception as e:
                error_msg = self._format_helpful_error(platform_config.name, str(e))
                print(error_msg)
                continue
        
        return balances
    
    def check_platform_balance(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Check balance for a specific platform"""
        platform_config = self.config_manager.get_platform(platform_name)
        if not platform_config:
            print(f"Platform {platform_name} not found in configuration")
            return None
        
        try:
            handler = self._get_handler(platform_config)
            balance_info = handler.get_balance()
            return {
                'platform': balance_info.platform,
                'balance': balance_info.balance,
                'currency': balance_info.currency,
                'raw_data': balance_info.raw_data
            }
        except Exception as e:
            error_msg = self._format_helpful_error(platform_name, str(e))
            print(error_msg)
            return None
    
    def _get_handler(self, config: PlatformConfig) -> BasePlatformHandler:
        """Get handler instance for platform configuration"""
        if config.name not in self.handlers:
            self.handlers[config.name] = create_handler(config, self.browser)
        return self.handlers[config.name]
    
    def list_platforms(self) -> List[str]:
        """List all available platforms"""
        return list(self.config_manager.platforms.keys())
    
    def list_enabled_platforms(self) -> List[str]:
        """List enabled platforms"""
        return [cfg.name for cfg in self.config_manager.get_enabled_platforms()]
    
    def format_balances(self, balances: List[Dict[str, Any]], format_type: str = 'table', target_currency: str = 'CNY') -> str:
        """Format balances in specified format"""
        return format_output(balances, format_type, target_currency)
    
    def _format_helpful_error(self, platform_name: str, error_message: str) -> str:
        """Format helpful error message for users"""
        error_lower = error_message.lower()
        
        # API Key missing errors
        if any(phrase in error_lower for phrase in ['api key required', 'api_key required', 'environment variable', 'not set']):
            env_var = self.config_manager.get_platform(platform_name).env_var
            return format_api_key_error(platform_name, env_var)
        
        # Authentication errors
        elif any(phrase in error_lower for phrase in ['authentication failed', 'unauthorized', 'invalid api', '401', '403']):
            return format_auth_error(platform_name, error_message)
        
        # Network errors
        elif any(phrase in error_lower for phrase in ['network error', 'connection', 'timeout', 'http error', '400', '404', '500']):
            return format_network_error(platform_name, error_message)
        
        # Generic error
        else:
            return f"❌ {platform_name}: {error_message}"

