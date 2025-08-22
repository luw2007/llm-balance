"""
Configuration management for LLM platforms
"""

import json
import yaml
from typing import Dict, Any, List
from pathlib import Path

class PlatformConfig:
    """Configuration for a single platform"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.api_url = config.get('api_url')
        self.method = config.get('method', 'GET')
        self.headers = config.get('headers', {})
        self.params = config.get('params', {})
        self.data = config.get('data', {})
        self.cookie_domain = config.get('cookie_domain')
        self.balance_path = config.get('balance_path', [])
        self.currency_path = config.get('currency_path', [])
        self.enabled = config.get('enabled', True)
        self.auth_type = config.get('auth_type', 'cookie')  # cookie, bearer_token, api_key, sdk
        self.env_var = config.get('env_var')  # environment variable name for API key
        self.region = config.get('region')  # region for SDK-based platforms
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'api_url': self.api_url,
            'method': self.method,
            'headers': self.headers,
            'params': self.params,
            'data': self.data,
            'cookie_domain': self.cookie_domain,
            'balance_path': self.balance_path,
            'currency_path': self.currency_path,
            'enabled': self.enabled,
            'auth_type': self.auth_type,
            'env_var': self.env_var,
            'region': self.region
        }

class ConfigManager:
    """Manages platform configurations"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or self._get_default_config_path()
        self.platforms = {}
        self.global_browser = 'arc'
        self.load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        home = Path.home()
        config_dir = home / '.llm_balance'
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / 'platforms.yaml')
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                # Load global browser configuration
                self.global_browser = config.get('browser', 'chrome')
                # Load platform configurations
                self.platforms = {
                    name: PlatformConfig(name, cfg)
                    for name, cfg in config.get('platforms', {}).items()
                }
        except FileNotFoundError:
            self._create_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.platforms = {}
    
    def _create_default_config(self):
        """Create default configuration"""
        default_config = {
            'browser': 'chrome',
            'platforms': {
                'deepseek': {
                    'api_url': 'https://api.deepseek.com/user/balance',
                    'method': 'GET',
                    'balance_path': ['balance_infos', 0, 'total_balance'],
                    'currency_path': ['balance_infos', 0, 'currency'],
                    'enabled': True,
                    'auth_type': 'bearer_token',
                    'env_var': 'DEEPSEEK_API_KEY',
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                },
                'moonshot': {
                    'api_url': 'https://api.moonshot.cn/v1/users/me/balance',
                    'method': 'GET',
                    'auth_type': 'bearer_token',
                    'env_var': 'MOONSHOT_API_KEY',
                    'enabled': False,
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                },
                'openai': {
                    'api_url': 'https://api.openai.com/v1/organization/costs',
                    'method': 'GET',
                    'balance_path': ['data', 0, 'results', 0, 'amount', 'value'],
                    'currency_path': ['data', 0, 'results', 0, 'amount', 'currency'],
                    'enabled': True,
                    'auth_type': 'bearer_token',
                    'env_var': 'OPENAI_ADMIN_KEY',
                    'params': {
                        'start_time': 1730419200,
                        'limit': 1
                    },
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                },
                'claude': {
                    'api_url': 'https://open.bigmodel.cn/api/anthropic/v1/messages',
                    'method': 'POST',
                    'balance_path': ['usage', 'input_tokens'],
                    'currency_path': 'USD',
                    'enabled': False,
                    'auth_type': 'bearer_token',
                    'env_var': 'ANTHROPIC_API_KEY',
                    'data': {
                        'max_tokens': 10,
                        'messages': [{'content': 'test', 'role': 'user'}],
                        'model': 'glm-4.5-air'
                    },
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'anthropic-version': '2023-06-01'
                    }
                },
                'volcengine': {
                    'api_url': 'https://console.volcengine.com/api/top/bill_volcano_engine/cn-north-1/2020-01-01/GetBalanceFromTradeBalance',
                    'method': 'POST',
                    'cookie_domain': 'console.volcengine.com',
                    'balance_path': ['Result', 'Acct', 'AvailableBalance'],
                    'currency_path': ['Result', 'Acct', 'Currency'],
                    'enabled': True,
                    'auth_type': 'cookie',  # Default to cookie authentication for backward compatibility
                    'region': 'cn-beijing',  # Default region for SDK authentication
                    'data': {
                        'ReqSysNo': 'page02',
                        'GetAlertFlag': 'Y'
                    },
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                },
                'aliyun': {
                    'api_url': 'https://bss.aliyuncs.com/',
                    'method': 'SDK',
                    'balance_path': ['Data', 'AvailableAmount'],
                    'currency_path': ['Data', 'Currency'],
                    'enabled': True,
                    'auth_type': 'bearer_token',
                    'env_var': 'ALIYUN_ACCESS_KEY_ID',
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    },
                    'params': {}
                },
                'gemini': {
                    'api_url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:countTokens',
                    'method': 'POST',
                    'balance_path': ['usage', 'total_tokens'],
                    'currency_path': 'USD',
                    'enabled': False,
                    'auth_type': 'api_key',
                    'env_var': 'GEMINI_API_KEY',
                    'headers': {
                        'Content-Type': 'application/json',
                        'x-goog-api-key': '${GEMINI_API_KEY}'
                    },
                    'data': {
                        'contents': [{
                            'parts': [{
                                'text': 'test'
                            }]
                        }]
                    }
                },
                'azure_openai': {
                    'api_url': 'https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CognitiveServices/accounts/{account_name}/usage?api-version=2023-05-01',
                    'method': 'GET',
                    'balance_path': ['value', 0, 'currentValue'],
                    'currency_path': ['value', 0, 'unit'],
                    'enabled': False,
                    'auth_type': 'bearer_token',
                    'env_var': 'AZURE_ACCESS_TOKEN',
                    'headers': {
                        'Authorization': 'Bearer ${AZURE_ACCESS_TOKEN}'
                    }
                },
                'tencent': {
                    'api_url': 'https://hunyuan.tencentcloudapi.com/',
                    'method': 'POST',
                    'balance_path': ['Response', 'Balance'],
                    'currency_path': ['Response', 'Currency'],
                    'enabled': False,
                    'auth_type': 'bearer_token',
                    'env_var': 'TENCENT_API_KEY',
                    'headers': {
                        'Authorization': 'Bearer ${TENCENT_API_KEY}',
                        'Content-Type': 'application/json',
                        'X-TC-Action': 'QueryBalance',
                        'X-TC-Version': '2023-09-01',
                        'X-TC-Region': 'ap-beijing'
                    },
                    'data': {}
                },
                'minimax': {
                    'api_url': 'https://api.minimax.chat/v1/account/balance',
                    'method': 'GET',
                    'balance_path': ['balance', 'total'],
                    'currency_path': ['balance', 'currency'],
                    'enabled': False,
                    'auth_type': 'bearer_token',
                    'env_var': 'MINIMAX_API_KEY',
                    'headers': {
                        'Authorization': 'Bearer ${MINIMAX_API_KEY}',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                },
                'lingyi': {
                    'api_url': 'https://api.lingyiwanwu.com/v1/account/balance',
                    'method': 'GET',
                    'balance_path': ['data', 'balance'],
                    'currency_path': ['data', 'currency'],
                    'enabled': False,
                    'auth_type': 'bearer_token',
                    'env_var': 'LINGYI_API_KEY',
                    'headers': {
                        'Authorization': 'Bearer ${LINGYI_API_KEY}',
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                },
                'zhipu': {
                    'api_url': 'https://bigmodel.cn/api/biz/account/query-customer-account-report',
                    'method': 'GET',
                    'balance_path': ['data', 'balance'],
                    'cookie_domain': '.bigmodel.cn',
                    'currency_path': 'CNY',
                    'enabled': True,
                    'auth_type': 'cookie',
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                }
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        self.platforms = {
            name: PlatformConfig(name, cfg)
            for name, cfg in default_config['platforms'].items()
        }
    
    def get_enabled_platforms(self) -> List[PlatformConfig]:
        """Get list of enabled platforms"""
        return [cfg for cfg in self.platforms.values() if cfg.enabled]
    
    def get_platform(self, name: str) -> PlatformConfig:
        """Get platform configuration by name"""
        return self.platforms.get(name)
    
    def update_platform(self, name: str, config: Dict[str, Any]):
        """Update platform configuration"""
        self.platforms[name] = PlatformConfig(name, config)
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        config = {
            'browser': self.global_browser,
            'platforms': {
                name: cfg.to_dict()
                for name, cfg in self.platforms.items()
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    def set_global_browser(self, browser: str):
        """Set global browser configuration"""
        supported_browsers = ['chrome', 'firefox', 'arc', 'brave', 'chromium']
        if browser not in supported_browsers:
            raise ValueError(f"Unsupported browser: {browser}. Supported browsers: {', '.join(supported_browsers)}")
        
        self.global_browser = browser
        self.save_config()
