"""
CLI interface for LLM Balance Checker
"""

import fire
from typing import Optional, List
from .balance_checker import BalanceChecker
from .utils import ensure_config_dir, get_exchange_rates
from .error_handler import get_setup_guide, format_platform_summary

class LLMBalanceCLI:
    """CLI interface for checking LLM platform balance and usage"""
    
    def __init__(self, config_file: str = None, browser: str = None):
        self.config_file = config_file
        self.browser = browser
        ensure_config_dir()
    
    def cost(self, platform: Optional[str] = None, 
              format: str = 'table', 
              browser: Optional[str] = None,
              currency: str = 'CNY') -> str:
        """
        Check balance for LLM platforms
        
        Args:
            platform: Specific platform to check (optional)
            format: Output format (json, markdown, table, total)
            browser: Browser to get cookies from (chrome, firefox, arc, brave, chromium)
            currency: Target currency for total (CNY, USD, EUR, etc.)
        
        Returns:
            Formatted balance information
        """
        # Use provided browser or fall back to CLI/browser constructor parameter
        browser = browser or self.browser
        
        # Create checker with the specified browser
        checker = BalanceChecker(self.config_file, browser)
        
        if platform:
            # Check specific platform
            balance = checker.check_platform_balance(platform)
            if balance:
                balances = [balance]
            else:
                return f"Could not get balance for {platform}"
        else:
            # Check all platforms
            balances = checker.check_all_balances()
        
        return checker.format_balances(balances, format, currency)
    
    def check(self, platform: Optional[str] = None, 
              format: str = 'table', 
              browser: Optional[str] = None,
              currency: str = 'CNY') -> str:
        """
        Check costs for LLM platforms (alias for cost command)
        
        Args:
            platform: Specific platform to check (optional)
            format: Output format (json, markdown, table, total)
            browser: Browser to get cookies from (chrome, firefox, arc, brave, chromium)
            currency: Target currency for total (CNY, USD, EUR, etc.)
        
        Returns:
            Formatted cost information
        """
        return self.cost(platform, format, browser, currency)
    
    def list(self) -> str:
        """List all available platforms"""
        checker = BalanceChecker(self.config_file, self.browser)
        platforms = checker.list_platforms()
        enabled = checker.list_enabled_platforms()
        
        result = "Available platforms:\n"
        for platform in platforms:
            status = "enabled" if platform in enabled else "disabled"
            result += f"  {platform} ({status})\n"
        
        return result
    
    def enable(self, platform: str) -> str:
        """Enable a platform or all platforms"""
        checker = BalanceChecker(self.config_file, self.browser)
        
        if platform.lower() == 'all':
            # Enable all platforms
            platforms = checker.config_manager.platforms
            enabled_count = 0
            for name, config in platforms.items():
                if not config.enabled:
                    config.enabled = True
                    enabled_count += 1
            
            if enabled_count > 0:
                checker.config_manager.save_config()
                return f"Enabled {enabled_count} platforms (all platforms)"
            else:
                return "All platforms are already enabled"
        else:
            # Enable specific platform
            config = checker.config_manager.get_platform(platform)
            if not config:
                return f"Platform {platform} not found"
            
            if config.enabled:
                return f"Platform {platform} is already enabled"
            
            config.enabled = True
            checker.config_manager.save_config()
            return f"Enabled {platform}"
    
    def disable(self, platform: str) -> str:
        """Disable a platform or all platforms"""
        checker = BalanceChecker(self.config_file, self.browser)
        
        if platform.lower() == 'all':
            # Disable all platforms
            platforms = checker.config_manager.platforms
            disabled_count = 0
            for name, config in platforms.items():
                if config.enabled:
                    config.enabled = False
                    disabled_count += 1
            
            if disabled_count > 0:
                checker.config_manager.save_config()
                return f"Disabled {disabled_count} platforms (all platforms)"
            else:
                return "All platforms are already disabled"
        else:
            # Disable specific platform
            config = checker.config_manager.get_platform(platform)
            if not config:
                return f"Platform {platform} not found"
            
            if not config.enabled:
                return f"Platform {platform} is already disabled"
            
            config.enabled = False
            checker.config_manager.save_config()
            return f"Disabled {platform}"
    
    def config(self, platform: str, key: str = None, value: str = None) -> str:
        """
        Configure platform settings
        
        Args:
            platform: Platform name
            key: Configuration key (optional)
            value: Configuration value (optional)
        """
        checker = BalanceChecker(self.config_file, self.browser)
        config = checker.config_manager.get_platform(platform)
        if not config:
            return f"Platform {platform} not found"
        
        if key is None:
            # Show all configuration
            import json
            return json.dumps(config.to_dict(), indent=2)
        
        if value is None:
            # Show specific key
            if hasattr(config, key):
                return f"{platform}.{key} = {getattr(config, key)}"
            else:
                return f"Key {key} not found in {platform} configuration"
        
        # Set configuration value
        config_dict = config.to_dict()
        if key in config_dict:
            # Convert string values to appropriate types
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
            
            config_dict[key] = value
            checker.config_manager.update_platform(platform, config_dict)
            return f"Set {platform}.{key} = {value}"
        else:
            return f"Key {key} not found in {platform} configuration"
    
    def set_browser(self, browser: str) -> str:
        """
        Set global browser configuration
        
        Args:
            browser: Browser name (chrome, firefox, arc, brave, chromium)
        
        Returns:
            Confirmation message
        """
        checker = BalanceChecker(self.config_file)
        
        try:
            # Set global browser in config
            checker.config_manager.set_global_browser(browser)
            # Update CLI default browser
            self.browser = browser
            
            return f"Global browser set to '{browser}'"
        except ValueError as e:
            return str(e)
    
    def rates(self) -> str:
        """Show current exchange rates"""
        rates = get_exchange_rates()
        
        result = "Current Exchange Rates (to CNY):\n"
        result += "=" * 40 + "\n"
        
        for currency, rate in sorted(rates.items()):
            result += f"{currency:<10} {rate:>10.4f}\n"
        
        result += "=" * 40 + "\n"
        result += "Customize rates with: LLM_BALANCE_RATES='{\"USD\": 7.2}'"
        
        return result
    
    def setup_guide(self) -> str:
        """Show complete setup guide for all platforms"""
        return get_setup_guide()
    
    def summary(self) -> str:
        """Show platform summary with quick setup commands"""
        return format_platform_summary()

def main():
    """Main CLI entry point"""
    fire.Fire(LLMBalanceCLI)

if __name__ == '__main__':
    main()
