"""
Main balance checker functionality
"""

import json
import threading
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import ConfigManager
from .platform_configs import PlatformConfig
from .platform_handlers.base import BasePlatformHandler, CostInfo
from .utils import get_nested_value, format_output, convert_currency, get_exchange_rates
from .platform_handlers import create_handler

class BalanceChecker:
    """Main balance checker class"""
    
    def __init__(self, config_file: str = None, browser: str = None):
        self.config_manager = ConfigManager(config_file)
        # Use provided browser or fall back to global configuration
        self.browser = browser or self.config_manager.get_global_browser()
        self.handlers = {}
        # Thread pool size for concurrent platform checking
        self.max_workers = 5
        # Thread lock for handler cache
        self._handler_lock = threading.Lock()

    def _check_single_balance(self, platform_config: PlatformConfig) -> Optional[Dict[str, Any]]:
        """Check balance for a single platform (thread-safe helper method)"""
        try:
            # Skip platforms with show_cost disabled
            if not platform_config.show_cost:
                return None

            handler = self._get_handler(platform_config)
            balance_info = handler.get_balance()
            return {
                'platform': balance_info.platform,
                'balance': balance_info.balance,
                'currency': balance_info.currency,
                'spent': balance_info.spent,
                'spent_currency': balance_info.spent_currency,
                'raw_data': balance_info.raw_data
            }
        except Exception as e:
            print(f"Error checking {platform_config.name}: {e}")
            return None

    def check_all_balances(self, sort: str = 'name') -> List[Dict[str, Any]]:
        """
        Check balances for all enabled platforms using thread pool

        Args:
            sort: Sort order for results - 'name' (alphabetical), 'balance' (descending), 'none' (as-is)
        """
        balances = []
        platforms = [p for p in self.config_manager.get_enabled_platforms() if p.show_cost]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all platform checks to thread pool
            future_to_platform = {
                executor.submit(self._check_single_balance, config): config
                for config in platforms
            }

            # Collect results as they complete
            for future in as_completed(future_to_platform):
                try:
                    result = future.result()
                    if result:
                        balances.append(result)
                except Exception as e:
                    platform = future_to_platform[future]
                    print(f"Error checking {platform.name}: {e}")

        # Apply sorting if requested
        if sort == 'name':
            # Sort alphabetically by platform name for consistent, predictable output
            balances.sort(key=lambda x: x['platform'].lower())
        elif sort == 'balance':
            # Sort by balance amount (descending) with currency conversion for fair comparison
            # Cache exchange rates to avoid repeated lookups
            rates = get_exchange_rates()
            def get_sort_key(item):
                # Use defensive .get() to avoid KeyError and provide sensible defaults
                balance_val = item.get('balance')
                currency = item.get('currency', 'CNY')

                # Handle None, '-', or other invalid values
                try:
                    balance = float(balance_val) if balance_val not in (None, '-') else 0.0
                except (ValueError, TypeError):
                    balance = 0.0

                # Convert to CNY for fair comparison across currencies
                try:
                    return convert_currency(balance, currency, 'CNY')
                except Exception:
                    # Fallback if conversion fails
                    return balance

            balances.sort(key=get_sort_key, reverse=True)
        elif sort == 'none':
            # Keep the as-is order (preserve concurrent execution order)
            pass

        return balances
    
    def check_platform_balance(self, platform_name: str) -> Optional[CostInfo]:
        """Check balance for a specific platform"""
        platform_config = self.config_manager.get_platform(platform_name)
        if not platform_config:
            print(f"Platform {platform_name} not found in configuration")
            return None

        # Check if cost display is disabled
        if hasattr(platform_config, 'show_cost') and not platform_config.show_cost:
            print(f"Cost display is disabled for platform {platform_name}")
            return None

        try:
            # self.config_manager.get_platform already returns PlatformConfig
            handler = self._get_handler(platform_config)
            return handler.get_balance()
        except Exception as e:
            print(f"Error checking {platform_name}: {e}")
            return None
    
    def _get_handler(self, config: PlatformConfig) -> BasePlatformHandler:
        """Get handler instance for platform configuration (thread-safe)"""
        # Use double-checked locking pattern for efficiency
        if config.name not in self.handlers:
            with self._handler_lock:
                # Check again after acquiring lock
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

