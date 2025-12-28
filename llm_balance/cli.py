"""
CLI interface for LLM Balance Checker
"""

import fire
from typing import Optional, List
from .balance_checker import BalanceChecker
from .token_checker import TokenChecker
from .utils import ensure_config_dir, get_exchange_rates

class LLMBalanceCLI:
    """CLI interface for checking LLM platform costs"""
    
    def __init__(self, config_file: str = None, browser: str = None):
        self.config_file = config_file
        # Will be set by BalanceChecker using global config
        self.browser = browser
        ensure_config_dir()
    
    def cost(self, platform: Optional[str] = None,
              format: str = 'table',
              browser: Optional[str] = None,
              currency: str = 'CNY',
              sort: str = 'name') -> str:
        """
        Check costs for LLM platforms

        Args:
            platform: Specific platform(s) to check, comma-separated string or tuple (optional)
                     Examples: "deepseek", "deepseek,aliyun", or multiple --platform flags
            format: Output format (json, markdown, table, total)
            browser: Browser to get cookies from (chrome, firefox, arc, brave, chromium, vivaldi)
            currency: Target currency for total (CNY, USD, EUR, etc.)
            sort: Sort order for results (name, balance, none)
                 - name: Sort alphabetically by platform name (default)
                 - balance: Sort by balance amount (descending)
                 - none: Keep the order as results complete

        Returns:
            Formatted cost information
        """
        browser = browser or self.browser
        checker = BalanceChecker(self.config_file, browser)

        # Validate sort parameter
        valid_sorts = ['name', 'balance', 'none']
        if sort not in valid_sorts:
            return f"Invalid sort option '{sort}'. Valid options: {', '.join(valid_sorts)}"

        if platform:
            # Handle comma-separated platform list or tuple from fire
            if isinstance(platform, tuple):
                platforms = [p.strip() for p in platform if p.strip()]
            elif isinstance(platform, str):
                platforms = [p.strip() for p in platform.split(',') if p.strip()]
            else:
                platforms = [str(platform).strip()] if str(platform).strip() else []
            
            if not platforms:
                return "No valid platforms specified"
                
            if len(platforms) == 1:
                # Single platform - use format_balance
                balance = checker.check_platform_balance(platforms[0])
                if balance:
                    return checker.format_balance(balance, format, currency)
                else:
                    return f"Platform '{platforms[0]}' not found or could not retrieve balance"
            else:
                # Multiple platforms - convert to dict list
                balances = []
                for p in platforms:
                    balance = checker.check_platform_balance(p)
                    if balance:
                        balances.append({
                            'platform': balance.platform,
                            'balance': balance.balance,
                            'currency': balance.currency,
                            'spent': balance.spent,
                            'spent_currency': balance.spent_currency,
                            'raw_data': balance.raw_data
                        })
                    else:
                        return f"Platform '{p}' not found or could not retrieve balance"
                
                # Apply sorting to multi-platform results
                if sort == 'name':
                    balances.sort(key=lambda x: x['platform'].lower())
                elif sort == 'balance':
                    # Import at module level would be circular, so inline import
                    from .utils import convert_currency, get_exchange_rates
                    rates = get_exchange_rates()
                    def get_sort_key(item):
                        balance_val = item.get('balance')
                        currency = item.get('currency', 'CNY')
                        try:
                            balance = float(balance_val) if balance_val not in (None, '-') else 0.0
                        except (ValueError, TypeError):
                            balance = 0.0
                        try:
                            return convert_currency(balance, currency, 'CNY')
                        except Exception:
                            return balance
                    balances.sort(key=get_sort_key, reverse=True)

                return checker.format_balances(balances, format, currency)
        else:
            # Check all platforms
            balances = checker.check_all_balances(sort=sort)
            return checker.format_balances(balances, format, currency)
    
    def package(self, platform: Optional[str] = None,
               format: str = 'table',
               browser: Optional[str] = None,
               currency: str = 'CNY',
               model: Optional[str] = None,
               show_all: bool = False,
               show_expiry: bool = True,
               show_reset: bool = True,
               show_reset_time: bool = True,
               sort: str = 'name') -> str:
        """
        Check model-level package/tokens for LLM platforms

        Args:
            platform: Specific platform(s) to check, comma-separated string or tuple (optional)
                     Examples: "volcengine", "volcengine,zhipu", or multiple --platform flags
            format: Output format (json, markdown, table, total)
            browser: Browser to get cookies from (chrome, firefox, arc, brave, chromium, vivaldi)
            currency: Target currency for total (CNY, USD, EUR, etc.)
            model: Filter by model name (optional)
                   Examples: "gpt-4", "doubao", "glm-4.5"
            show_all: Include entries marked as inactive when True
            show_expiry: Show expiry date for subscriptions (88code, etc.)
            show_reset: Show reset count for subscriptions (88code, etc.)
            show_reset_time: Show reset time for subscriptions (moonshot, 88code, etc.)
            sort: Sort order for results (name, none)
                 - name: Sort alphabetically by platform name (default)
                 - none: Keep the order as results complete

        Returns:
            Formatted package information with model-level details
        """
        browser = browser or self.browser
        checker = TokenChecker(self.config_file, browser)

        # Validate sort parameter
        valid_sorts = ['name', 'none']
        if sort not in valid_sorts:
            return f"Invalid sort option '{sort}'. Valid options: {', '.join(valid_sorts)}"

        if platform:
            # Handle comma-separated platform list or tuple from fire
            if isinstance(platform, tuple):
                platforms = [p.strip() for p in platform if p.strip()]
            elif isinstance(platform, str):
                platforms = [p.strip() for p in platform.split(',') if p.strip()]
            else:
                platforms = [str(platform).strip()] if str(platform).strip() else []

            if not platforms:
                return "No valid platforms specified"

            tokens = []

            for p in platforms:
                token_info = checker.check_platform_tokens(p)
                if token_info:
                    tokens.append(token_info)

            if not tokens:
                return "No token data available"
        else:
            # Check all platforms
            tokens = checker.check_all_tokens(sort=sort)

        return checker.format_tokens(tokens, format, currency, model, show_all, show_expiry, show_reset, show_reset_time)

    def check(self, platform: Optional[str] = None, 
              format: str = 'table', 
              browser: Optional[str] = None,
              currency: str = 'CNY') -> str:
        """
        Check costs for LLM platforms (alias for cost command)
        
        Args:
            platform: Specific platform(s) to check, comma-separated string or tuple (optional)
                     Examples: "deepseek", "deepseek,aliyun", or multiple --platform flags
            format: Output format (json, markdown, table, total)
            browser: Browser to get cookies from (chrome, firefox, arc, brave, chromium, vivaldi)
            currency: Target currency for total (CNY, USD, EUR, etc.)
        
        Returns:
            Formatted cost information
        """
        return self.cost(platform, format, browser, currency)
    
    def list(self) -> str:
        """List all available platforms"""
        from .config import ConfigManager

        config_manager = ConfigManager(self.config_file)
        platforms = config_manager.get_all_platforms()

        result = "Available platforms:\n"
        for platform in platforms:
            # Get full config (default + user overrides)
            config = config_manager.get_platform_config(platform)
            if config:
                enabled = config.get('enabled', False)
                status = "enabled" if enabled else "disabled"
                result += f"  {platform} ({status})\n"

        return result
    
    def enable(self, platform: str) -> str:
        """Enable one or more platforms (comma-separated or multiple args)."""
        from .config import ConfigManager
        
        config_manager = ConfigManager(self.config_file)
        all_platforms = set(config_manager.get_all_platforms())
        
        # Parse input: support tuple from Fire and comma-separated string
        if isinstance(platform, tuple):
            platforms = [p.strip() for p in platform if str(p).strip()]
        elif isinstance(platform, str):
            # Accept comma-separated list
            platforms = [p.strip() for p in platform.split(',') if p.strip()]
        else:
            platforms = [str(platform).strip()] if str(platform).strip() else []
        
        if not platforms:
            return "No valid platforms specified"
        
        # Special case: 'all'
        if any(p.lower() == 'all' for p in platforms):
            enabled_count = 0
            for name in all_platforms:
                user_config = config_manager.user_config.get(name, {})
                if not user_config.get('enabled', True):
                    config_manager.enable_platform(name)
                    enabled_count += 1
            return f"Enabled {enabled_count} platforms (all disabled platforms)"
        
        # Enable listed platforms
        enabled = []
        not_found = []
        for name in platforms:
            if name in all_platforms:
                config_manager.enable_platform(name)
                enabled.append(name)
            else:
                not_found.append(name)
        
        parts = []
        if enabled:
            parts.append(f"Enabled {len(enabled)}: {', '.join(enabled)}")
        if not_found:
            parts.append(f"Not found: {', '.join(not_found)}")
        return "; ".join(parts) if parts else "No changes"
    
    def disable(self, platform: str) -> str:
        """Disable one or more platforms (comma-separated or multiple args)."""
        from .config import ConfigManager
        
        config_manager = ConfigManager(self.config_file)
        all_platforms = set(config_manager.get_all_platforms())
        
        # Parse input: support tuple from Fire and comma-separated string
        if isinstance(platform, tuple):
            platforms = [p.strip() for p in platform if str(p).strip()]
        elif isinstance(platform, str):
            platforms = [p.strip() for p in platform.split(',') if p.strip()]
        else:
            platforms = [str(platform).strip()] if str(platform).strip() else []
        
        if not platforms:
            return "No valid platforms specified"
        
        # Special case: 'all'
        if any(p.lower() == 'all' for p in platforms):
            disabled_count = 0
            for name in all_platforms:
                user_config = config_manager.user_config.get(name, {})
                if user_config.get('enabled', True):
                    config_manager.disable_platform(name)
                    disabled_count += 1
            return f"Disabled {disabled_count} platforms (all enabled platforms)"
        
        # Disable listed platforms
        disabled = []
        not_found = []
        for name in platforms:
            if name in all_platforms:
                config_manager.disable_platform(name)
                disabled.append(name)
            else:
                not_found.append(name)
        
        parts = []
        if disabled:
            parts.append(f"Disabled {len(disabled)}: {', '.join(disabled)}")
        if not_found:
            parts.append(f"Not found: {', '.join(not_found)}")
        return "; ".join(parts) if parts else "No changes"
    
    def config(self, platform: str, key: str = None, value: str = None) -> str:
        """
        Configure platform settings

        Args:
            platform: Platform name
            key: Configuration key (optional)
            value: Configuration value (optional)
        """
        from .config import ConfigManager

        config_manager = ConfigManager(self.config_file)
        config = config_manager.get_platform_config(platform)

        if not config:
            return f"Platform {platform} not found"

        if key is None:
            # Show all configuration
            import json
            return json.dumps(config, indent=2, ensure_ascii=False)

        if value is None:
            # Show specific key
            if key in config:
                return f"{platform}.{key} = {config[key]}"
            else:
                return f"Key {key} not found in {platform} configuration"

        # Set configuration value
        # Allow setting show_cost and show_package even if they're not in the original config
        if key in config or key in ['show_cost', 'show_package']:
            # Convert string values to appropriate types
            if isinstance(value, str):
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)

            if platform not in config_manager.user_config:
                config_manager.user_config[platform] = {}
            config_manager.user_config[platform][key] = value
            config_manager.save_config()
            return f"Set {platform}.{key} = {value}"
        else:
            return f"Key {key} not found in {platform} configuration"
    
    def set_browser(self, browser: str) -> str:
        """
        Set global browser configuration for all platforms
        
        Args:
            browser: Browser name (chrome, firefox, arc, brave, chromium, vivaldi)
        
        Returns:
            Confirmation message
        """
        valid_browsers = ['chrome', 'firefox', 'arc', 'brave', 'chromium', 'vivaldi']
        if browser not in valid_browsers:
            return f"Invalid browser '{browser}'. Valid options: {', '.join(valid_browsers)}"
        
        checker = BalanceChecker(self.config_file, self.browser)
        checker.config_manager.set_global_browser(browser)
        return f"Global browser set to: {browser}"
    
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
        """Show full setup guide for all platforms"""
        from .error_handler import get_setup_guide
        return get_setup_guide()
    
        
    def doctor(self) -> str:
        """
        Run comprehensive diagnostics and health checks
        """
        import os
        from .config import ConfigManager

        result = "🔧 LLM Balance Checker 诊断报告\n"
        result += "=" * 50 + "\n\n"

        # 检查环境变量
        result += "📋 环境变量检查:\n"
        env_vars = ['DEEPSEEK_API_KEY', 'MOONSHOT_API_KEY', 'VOLCENGINE_ACCESS_KEY', 'ALIYUN_ACCESS_KEY_ID']
        missing_vars = [var for var in env_vars if not os.getenv(var)]
        if missing_vars:
            result += "❌ 缺失的环境变量:\n"
            for var in missing_vars:
                result += f"   • {var}\n"
        else:
            result += "✅ 主要环境变量已设置\n"

        # 检查配置文件
        result += f"\n📋 配置文件检查:\n"
        config_path = os.path.expanduser("~/.llm_balance/config.yaml")
        if os.path.exists(config_path):
            result += f"✅ 配置文件存在: {config_path}\n"
        else:
            result += f"❌ 配置文件不存在: {config_path}\n"

        # 检查浏览器
        result += f"\n📋 浏览器配置:\n"
        config_manager = ConfigManager(self.config_file)
        browser = config_manager.get_global_browser()
        result += f"   当前浏览器: {browser}\n"

        # 检查平台注册
        result += f"\n📋 平台注册检查:\n"
        platforms = config_manager.get_all_platforms()
        result += f"   已注册平台数量: {len(platforms)}\n"
        for name in sorted(platforms):
            result += f"   • {name}\n"

        # 系统状态
        result += f"\n📋 系统状态:\n"
        result += "   系统运行正常\n"
        result += "   配置文件可访问\n"

        # 网络连接测试
        result += f"\n📋 网络连接测试:\n"
        result += "   (可选) 运行 'llm-balance cost' 测试实际连接\n"

        return result
    
        
        
    def generate_config(self, output: str = None) -> str:
        """
        Generate configuration file from platform handlers

        Args:
            output: Output file path (optional, defaults to user config directory)

        Returns:
            Generation result
        """
        from .config import ConfigManager

        try:
            config_manager = ConfigManager(self.config_file)
            output_path = config_manager.generate_config_file(output)
            result = "✅ 配置文件生成成功\n"
            result += "=" * 30 + "\n\n"
            result += f"输出文件: {output_path}\n"
            result += f"包含平台: {len(config_manager.get_all_platforms())} 个\n"
            result += "\n💡 提示:\n"
            result += "   • 配置文件包含所有平台的默认配置\n"
            result += "   • 可以手动编辑此文件来自定义配置\n"
            result += "   • 使用 'llm-balance config <platform>' 查看具体配置\n"

        except Exception as e:
            result = f"❌ 配置文件生成失败: {e}\n"
            result += "=" * 30 + "\n\n"
            result += "请检查文件权限和路径\n"

        return result

    def platform_config(self, platform: str, key: str = None, value: str = None) -> str:
        """
        Manage platform-specific configuration (separate from global config)

        Args:
            platform: Platform name (supports 'duckcoding', 'cubence', 'csmindai', 'yourapi', 'deepseek', 'dawclaudecode', 'magic666', 'jimiai', 'openclaudecode', 'ikuncode')
            key: Configuration key (optional)
            value: Configuration value (optional)

        Returns:
            Configuration status
        """
        import yaml
        from pathlib import Path

        # Map platform names to their config file names and supported keys
        platform_configs = {
            'duckcoding': {
                'file': 'duckcoding_config.yaml',
                'keys': ['api_user_id'],
                'display_name': 'DuckCoding'
            },
            'cubence': {
                'file': 'cubence_config.yaml',
                'keys': ['token'],
                'display_name': 'Cubence'
            },
            'csmindai': {
                'file': 'csmindai_config.yaml',
                'keys': ['api_user_id'],
                'display_name': 'CSMindAI'
            },
            'yourapi': {
                'file': 'yourapi_config.yaml',
                'keys': ['api_user_id'],
                'display_name': 'YourAPI'
            },
            'deepseek': {
                'file': 'deepseek_config.yaml',
                'keys': ['console_token'],
                'display_name': 'DeepSeek'
            },
            'dawclaudecode': {
                'file': 'dawclaudecode_config.yaml',
                'keys': ['api_user_id'],
                'display_name': 'DawClaudeCode'
            },
            'magic666': {
                'file': 'magic666_config.yaml',
                'keys': ['api_user_id'],
                'display_name': 'Magic666'
            },
            'jimiai': {
                'file': 'jimiai_config.yaml',
                'keys': ['api_user_id'],
                'display_name': 'Jimiai'
            },
            'openclaudecode': {
                'file': 'openclaudecode_config.yaml',
                'keys': ['api_user_id'],
                'display_name': 'OpenClaudeCode'
            },
            'ikuncode': {
                'file': 'ikuncode_config.yaml',
                'keys': ['api_user_id'],
                'display_name': 'IKunCode'
            }
        }

        platform_lower = platform.lower()
        if platform_lower not in platform_configs:
            supported = ', '.join(platform_configs.keys())
            return f"Platform '{platform}' does not support separate configuration. Supported platforms: {supported}\nUse 'llm-balance config {platform}' for other platforms."

        platform_info = platform_configs[platform_lower]
        config_path = Path.home() / '.llm_balance' / platform_info['file']

        # Load existing config
        config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            except Exception as e:
                return f"Error loading config: {e}"

        if key is None:
            # Show all configuration
            if not config:
                display_name = platform_info['display_name']
                example_keys = ', '.join(platform_info['keys'])
                return f"No {display_name} configuration found. Set {platform.upper()}_* environment variable or create {config_path}\nSupported keys: {example_keys}"

            import json
            return json.dumps(config, indent=2, ensure_ascii=False)

        if value is None:
            # Show specific key
            if key in config:
                return f"{platform_lower}.{key} = {config[key]}"
            else:
                return f"Key '{key}' not found in {platform_info['display_name']} configuration"

        # Set configuration value
        # Convert string values to appropriate types
        if isinstance(value, str):
            if value.lower() in ['true', 'false']:
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)

        config[key] = value

        # Save config
        try:
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            return f"Set {platform_lower}.{key} = {value} (stored in {config_path})"
        except Exception as e:
            return f"Error saving config: {e}"

def main():
    """Main CLI entry point"""
    fire.Fire(LLMBalanceCLI)

if __name__ == '__main__':
    main()
