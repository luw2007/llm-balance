"""
Main balance checker functionality
"""

import json
from typing import List, Dict, Any, Optional
from .config import ConfigManager
from .platform_configs import PlatformConfig
from .platform_handlers.base import BasePlatformHandler, CostInfo
from .utils import get_nested_value, format_output
from .platform_handlers import create_handler

class BalanceChecker:
    """Main balance checker class"""
    
    def __init__(self, config_file: str = None, browser: str = None):
        self.config_manager = ConfigManager(config_file)
        # Use provided browser or fall back to global configuration
        self.browser = browser or self.config_manager.get_global_browser()
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
                    'spent': balance_info.spent,
                    'spent_currency': balance_info.spent_currency,
                    'raw_data': balance_info.raw_data
                })
            except Exception as e:
                print(f"Error checking {platform_config.name}: {e}")
                continue
        
        return balances
    
    def check_platform_balance(self, platform_name: str) -> Optional[CostInfo]:
        """Check balance for a specific platform"""
        platform_config = self.config_manager.get_platform(platform_name)
        if not platform_config:
            print(f"Platform {platform_name} not found in configuration")
            return None
        
        try:
            # Convert dict config to PlatformConfig if needed
            if isinstance(platform_config, dict):
                platform_config = PlatformConfig(
                    name=platform_name,
                    display_name=platform_config.get('display_name', platform_name.title()),
                    handler_class=platform_config.get('handler_class', f'{platform_name.title()}Handler'),
                    description=platform_config.get('description', f'{platform_name.title()} platform'),
                    auth_type=platform_config.get('auth_type', 'api_key'),
                    enabled=platform_config.get('enabled', True),
                    **{k: v for k, v in platform_config.items() if k not in ['name', 'display_name', 'handler_class', 'description', 'auth_type', 'enabled']}
                )
            
            handler = self._get_handler(platform_config)
            return handler.get_balance()
        except Exception as e:
            print(f"Error checking {platform_name}: {e}")
            return None
    
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
    
    def format_balances(self, balances: List[Dict[str, Any]], format_type: str = 'table', target_currency: str = 'CNY') -> str:
        """Format balances in specified format"""
        return format_output(balances, format_type, target_currency)
    
    def format_balance(self, balance: CostInfo, format_type: str = 'table', target_currency: str = 'CNY') -> str:
        """Format a single balance in specified format"""
        balance_dict = {
            'platform': balance.platform,
            'balance': balance.balance,
            'currency': balance.currency,
            'spent': balance.spent,
            'spent_currency': balance.spent_currency,
            'raw_data': balance.raw_data
        }
        return format_output([balance_dict], format_type, target_currency)

