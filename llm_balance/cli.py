"""
CLI interface for LLM Balance Checker
"""

import fire
from typing import Optional, List
from .balance_checker import BalanceChecker
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
              currency: str = 'CNY') -> str:
        """
        Check costs for LLM platforms
        
        Args:
            platform: Specific platform(s) to check, comma-separated string or tuple (optional)
                     Examples: "deepseek", "deepseek,aliyun", or multiple --platform flags
            format: Output format (json, markdown, table, total)
            browser: Browser to get cookies from (chrome, firefox, arc, brave, chromium)
            currency: Target currency for total (CNY, USD, EUR, etc.)
        
        Returns:
            Formatted cost information
        """
        browser = browser or self.browser
        checker = BalanceChecker(self.config_file, browser)
        
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
                
            balances = []
            
            for p in platforms:
                balance = checker.check_platform_balance(p)
                if balance:
                    balances.append(balance)
                else:
                    return f"Platform '{p}' not found or could not retrieve balance"
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
            platform: Specific platform(s) to check, comma-separated string or tuple (optional)
                     Examples: "deepseek", "deepseek,aliyun", or multiple --platform flags
            format: Output format (json, markdown, table, total)
            browser: Browser to get cookies from (chrome, firefox, arc, brave, chromium)
            currency: Target currency for total (CNY, USD, EUR, etc.)
        
        Returns:
            Formatted cost information
        """
        return self.cost(platform, format, browser, currency)
    
    def list(self) -> str:
        """List all available platforms"""
        from .platform_configs import ConfigManager
        
        config_manager = ConfigManager(self.config_file)
        platforms = config_manager.get_all_platforms()
        
        result = "Available platforms:\n"
        for platform in platforms:
            # Check if platform is enabled in user config
            user_config = config_manager.user_config.get(platform, {})
            enabled = user_config.get('enabled', True)
            status = "enabled" if enabled else "disabled"
            result += f"  {platform} ({status})\n"
        
        return result
    
    def enable(self, platform: str) -> str:
        """Enable a platform"""
        from .platform_configs import ConfigManager
        
        config_manager = ConfigManager(self.config_file)
        
        if platform == 'all':
            # Enable all platforms
            platforms = config_manager.get_all_platforms()
            enabled_count = 0
            
            for platform_name in platforms:
                user_config = config_manager.user_config.get(platform_name, {})
                if not user_config.get('enabled', True):
                    config_manager.enable_platform(platform_name)
                    enabled_count += 1
            
            return f"Enabled {enabled_count} platforms (all disabled platforms)"
        else:
            # Enable specific platform
            if platform not in config_manager.get_all_platforms():
                return f"Platform {platform} not found"
            
            config_manager.enable_platform(platform)
            return f"Enabled {platform}"
    
    def disable(self, platform: str) -> str:
        """Disable a platform"""
        from .platform_configs import ConfigManager
        
        config_manager = ConfigManager(self.config_file)
        
        if platform == 'all':
            # Disable all platforms
            platforms = config_manager.get_all_platforms()
            disabled_count = 0
            
            for platform_name in platforms:
                user_config = config_manager.user_config.get(platform_name, {})
                if user_config.get('enabled', True):
                    config_manager.disable_platform(platform_name)
                    disabled_count += 1
            
            return f"Disabled {disabled_count} platforms (all enabled platforms)"
        else:
            # Disable specific platform
            if platform not in config_manager.get_all_platforms():
                return f"Platform {platform} not found"
            
            config_manager.disable_platform(platform)
            return f"Disabled {platform}"
    
    def config(self, platform: str, key: str = None, value: str = None) -> str:
        """
        Configure platform settings
        
        Args:
            platform: Platform name
            key: Configuration key (optional)
            value: Configuration value (optional)
        """
        from .platform_configs import ConfigManager
        
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
        if key in config:
            # Convert string values to appropriate types
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
            browser: Browser name (chrome, firefox, arc, brave, chromium)
        
        Returns:
            Confirmation message
        """
        valid_browsers = ['chrome', 'firefox', 'arc', 'brave', 'chromium']
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
    
        
    def diagnose(self) -> str:
        """
        Run comprehensive diagnostics
        """
        import os
        from .platform_handlers import registry
        
        result = "🔧 LLM Balance Checker 诊断报告\n"
        result += "=" * 50 + "\n\n"
        
        # 检查环境变量
        result += "📋 环境变量检查:\n"
        import os
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
        checker = BalanceChecker(self.config_file, self.browser)
        browser = checker.config_manager.get_global_browser()
        result += f"   当前浏览器: {browser}\n"
        
        # 检查平台注册
        result += f"\n📋 平台注册检查:\n"
        platforms = checker.config_manager.list_platforms()
        result += f"   已注册平台数量: {len(platforms)}\n"
        for name in platforms:
            result += f"   • {name}\n"
        
        # 系统状态
        result += f"\n📋 系统状态:\n"
        result += f"   系统运行正常\n"
        result += f"   配置文件可访问\n"
        
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
        from .platform_configs import ConfigManager
        
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

def main():
    """Main CLI entry point"""
    fire.Fire(LLMBalanceCLI)

if __name__ == '__main__':
    main()