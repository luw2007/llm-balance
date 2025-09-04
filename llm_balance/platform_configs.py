"""
Platform configuration management
Default configurations are maintained in Python code, with generation to YAML
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class PlatformConfig:
    """Platform configuration data class"""
    name: str
    display_name: str
    handler_class: str
    description: str
    auth_type: str
    default_enabled: bool = True
    env_var: Optional[str] = None
    
    # API configuration
    api_url: str = ""
    method: str = "GET"
    headers: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Authentication configuration
    cookie_domain: Optional[str] = None
    region: Optional[str] = None
    
    # Legacy compatibility fields
    balance_path: Optional[list] = None
    currency_path: Optional[str] = None
    browser: Optional[str] = None
    
    # Status
    enabled: bool = True
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.params is None:
            self.params = {}
        if self.data is None:
            self.data = {}
        if self.balance_path is None:
            self.balance_path = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            'name': self.name,
            'display_name': self.display_name,
            'handler_class': self.handler_class,
            'description': self.description,
            'auth_type': self.auth_type,
            'default_enabled': self.default_enabled,
            'enabled': self.enabled,
        }
        
        if self.env_var:
            result['env_var'] = self.env_var
            
        if self.api_url:
            result['api_url'] = self.api_url
            result['method'] = self.method
            
        if self.headers:
            result['headers'] = self.headers
            
        if self.params:
            result['params'] = self.params
            
        if self.data:
            result['data'] = self.data
            
        if self.cookie_domain:
            result['cookie_domain'] = self.cookie_domain
            
        if self.region:
            result['region'] = self.region
            
        # Legacy compatibility
        if self.balance_path:
            result['balance_path'] = self.balance_path
        if self.currency_path:
            result['currency_path'] = self.currency_path
        if self.browser:
            result['browser'] = self.browser
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlatformConfig':
        """Create from dictionary"""
        return cls(**data)


class ConfigManager:
    """Simplified configuration manager using platform handlers"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or self._get_default_config_path()
        self.global_config: Dict[str, Any] = {'browser': 'chrome'}
        self.user_config: Dict[str, Any] = {}
        self.load_user_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        home = Path.home()
        config_dir = home / '.llm_balance'
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / 'config.yaml')
    
    def load_user_config(self):
        """Load user configuration from file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                self.user_config = config.get('platforms', {})
                self.global_config['browser'] = config.get('browser', 'chrome')
        except FileNotFoundError:
            self.user_config = {}
        except Exception as e:
            print(f"Error loading user config: {e}")
            self.user_config = {}
    
    def get_platform_config(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get platform configuration directly from handler"""
        from .platform_handlers import (
            DeepSeekHandler, MoonshotHandler, VolcengineHandler,
            AliyunHandler, TencentHandler, ZhipuHandler, SiliconFlowHandler
        )
        
        handler_map = {
            'deepseek': DeepSeekHandler,
            'moonshot': MoonshotHandler,
            'volcengine': VolcengineHandler,
            'aliyun': AliyunHandler,
            'tencent': TencentHandler,
            'zhipu': ZhipuHandler,
            'siliconflow': SiliconFlowHandler,
        }
        
        if platform_name not in handler_map:
            return None
        
        try:
            handler_class = handler_map[platform_name]
            config = handler_class.get_default_config()
            
            # Apply user overrides
            user_override = self.user_config.get(platform_name, {})
            config.update(user_override)
            
            return config
        except Exception as e:
            print(f"Error getting config for {platform_name}: {e}")
            return None
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            'browser': self.global_config.get('browser', 'chrome'),
            'platforms': self.user_config
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    def get_all_platforms(self) -> List[str]:
        """Get all available platform names"""
        return ['deepseek', 'moonshot', 'volcengine', 'aliyun', 'tencent', 'zhipu', 'siliconflow']
    
    def get_enabled_platforms(self) -> List[PlatformConfig]:
        """Get enabled platform configurations"""
        enabled_platforms = []
        
        for platform_name in self.get_all_platforms():
            config = self.get_platform_config(platform_name)
            if config and config.get('enabled', True):
                # Create PlatformConfig object
                platform_config = PlatformConfig(
                    name=platform_name,
                    display_name=config.get('display_name', platform_name.title()),
                    handler_class=config.get('handler_class', f'{platform_name.title()}Handler'),
                    description=config.get('description', f'{platform_name.title()} platform'),
                    auth_type=config.get('auth_type', 'api_key'),
                    enabled=config.get('enabled', True),
                    **{k: v for k, v in config.items() if k not in ['name', 'display_name', 'handler_class', 'description', 'auth_type', 'enabled']}
                )
                enabled_platforms.append(platform_config)
        
        return enabled_platforms
    
    def enable_platform(self, platform_name: str):
        """Enable a platform"""
        if platform_name not in self.user_config:
            self.user_config[platform_name] = {}
        self.user_config[platform_name]['enabled'] = True
        self.save_config()
    
    def disable_platform(self, platform_name: str):
        """Disable a platform"""
        if platform_name not in self.user_config:
            self.user_config[platform_name] = {}
        self.user_config[platform_name]['enabled'] = False
        self.save_config()
    
    def get_global_config(self) -> Dict[str, Any]:
        """Get global configuration"""
        return self.global_config
    
    def set_global_config(self, key: str, value: Any):
        """Set global configuration"""
        self.global_config[key] = value
        self.save_config()
    
    def generate_config_file(self, output_file: str = None) -> str:
        """Generate a complete configuration file from all platform configs"""
        if output_file is None:
            output_file = self.config_file
        
        config = {
            'browser': self.global_config.get('browser', 'chrome'),
            'platforms': {}
        }
        
        # Get configurations from handlers
        from .platform_handlers import (
            DeepSeekHandler, MoonshotHandler, VolcengineHandler,
            AliyunHandler, TencentHandler, ZhipuHandler, SiliconFlowHandler
        )
        
        handler_map = {
            'deepseek': DeepSeekHandler,
            'moonshot': MoonshotHandler,
            'volcengine': VolcengineHandler,
            'aliyun': AliyunHandler,
            'tencent': TencentHandler,
            'zhipu': ZhipuHandler,
            'siliconflow': SiliconFlowHandler,
        }
        
        for name, handler_class in handler_map.items():
            try:
                default_config = handler_class.get_default_config()
                config['platforms'][name] = default_config
                
                # Apply user overrides
                if name in self.user_config:
                    config['platforms'][name].update(self.user_config[name])
                    
            except Exception as e:
                print(f"Warning: Failed to generate config for {name}: {e}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        return output_file