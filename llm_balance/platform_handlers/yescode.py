"""
YesCode platform handler
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import BasePlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo, CodingPlanInfo, CodingPlanQuota
from ..config import PlatformConfig

class YesCodeHandler(BasePlatformHandler):
    """YesCode platform cost handler
    
    YesCode 是一个 API 中继平台,使用 API Key (Bearer Token) 认证方式。
    支持订阅制模型,包括 daily/weekly/monthly 限额。
    """
    
    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for YesCode platform"""
        return {
            "api_url": "https://api.yescode.cloud/api/v1/subscriptions",
            "official_url": "https://api.yescode.cloud",
            "api_management_url": "https://api.yescode.cloud/keys",
            "method": "GET",
            "auth_type": "bearer_token",
            "env_var": "YESCODE_API_KEY",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "params": {"timezone": "Asia/Shanghai"},
            "data": {},
            "setup_steps": [
                '访问 https://api.yescode.cloud 并注册/登录',
                '进入 "API Keys" 页面',
                '点击 "创建密钥" 创建新的 API Key',
                '复制生成的 API Key',
                '设置环境变量: export YESCODE_API_KEY="your_api_key"'
            ],
            "notes": [
                'API Key 使用 Bearer Token 认证',
                '支持标准 OpenAI 兼容接口 (/v1/messages)',
                '套餐包含每日/周/月额度',
                '查看仪表盘了解余额、并发限制等信息',
                '支持 Claude Code/Plan 模型 (根据 claude_code_only 字段识别)'
            ],
            "enabled": True
        }
    
    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        self._load_env_config()
    
    def _load_env_config(self):
        """Load configuration from ~/.llm_balance/yescode_config.yaml"""
        if os.getenv('YESCODE_API_KEY') or os.getenv('YESCODE_API_TOKEN'):
            return
        
        try:
            import yaml
            from pathlib import Path
            
            config_path = Path.home() / '.llm_balance' / 'yescode_config.yaml'
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    yescode_config = yaml.safe_load(f) or {}
                    
                    if 'console_token' in yescode_config:
                        os.environ['YESCODE_API_KEY'] = yescode_config['console_token']
                    elif 'api_key' in yescode_config:
                        os.environ['YESCODE_API_KEY'] = yescode_config['api_key']
        except Exception:
            pass

    def get_balance(self) -> CostInfo:
        """Get cost information from YesCode"""
        response = self._make_yescode_request()
        
        balance = self._extract_balance(response)
        spent = self._extract_spent(response)
        currency = self._extract_currency(response)
        
        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'USD',
            spent=spent,
            spent_currency=currency or 'USD',
            raw_data=response
        )
    
    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "YesCode"
    
    def _make_yescode_request(self) -> Dict[str, Any]:
        """Make API request to YesCode with proper authentication"""
        api_key = os.getenv('YESCODE_API_KEY') or os.getenv('YESCODE_API_TOKEN')
        
        if not api_key:
            raise ValueError("YesCode API key required. Set YESCODE_API_KEY or YESCODE_API_TOKEN environment variable.")
        
        headers = self.config.headers.copy() if self.config.headers else {}
        headers['Authorization'] = f'Bearer {api_key}'
        
        api_url = f"{self.config.api_url}?timezone=Asia/Shanghai"
        
        response = self._make_request(
            url=api_url,
            method=self.config.method,
            headers=headers
        )
        
        if not response:
            raise ValueError("No response from YesCode API")
        
        return response
    
    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from YesCode API response"""
        try:
            if response.get('code') != 0:
                return 0.0
            
            subscriptions = response.get('data', [])
            if not isinstance(subscriptions, list) or not subscriptions:
                return 0.0
            
            total_remaining = 0.0
            
            for sub in subscriptions:
                if sub.get('status') != 'active':
                    continue
                
                group = sub.get('group', {})
                
                daily_limit = float(group.get('daily_limit_usd', 0))
                weekly_limit = float(group.get('weekly_limit_usd', 0))
                monthly_limit = float(group.get('monthly_limit_usd', 0))
                
                daily_used = float(sub.get('daily_usage_usd', 0))
                weekly_used = float(sub.get('weekly_usage_usd', 0))
                monthly_used = float(sub.get('monthly_usage_usd', 0))
                
                daily_remaining = max(0, daily_limit - daily_used)
                weekly_remaining = max(0, weekly_limit - weekly_used)
                monthly_remaining = max(0, monthly_limit - monthly_used)
                
                remaining = min(
                    daily_remaining if daily_limit > 0 else float('inf'),
                    weekly_remaining if weekly_limit > 0 else float('inf'),
                    monthly_remaining if monthly_limit > 0 else float('inf')
                )
                
                if remaining != float('inf'):
                    total_remaining += remaining
            
            return self._validate_balance(total_remaining, "balance")
            
        except (ValueError, TypeError, KeyError) as e:
            print(f"Warning: Failed to extract balance: {e}")
            return 0.0
    
    def _extract_spent(self, response: Dict[str, Any]) -> float:
        """Extract spent amount from YesCode API response"""
        try:
            if response.get('code') != 0:
                return 0.0
            
            subscriptions = response.get('data', [])
            if not isinstance(subscriptions, list):
                return 0.0
            
            total_spent = 0.0
            
            for sub in subscriptions:
                if sub.get('status') != 'active':
                    continue
                
                monthly_used = float(sub.get('monthly_usage_usd', 0))
                total_spent += monthly_used
            
            return total_spent
            
        except (ValueError, TypeError, KeyError):
            return 0.0
    
    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from YesCode API response"""
        return 'USD'

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get model-level token information from YesCode"""
        response = self._make_yescode_request()
        
        model_tokens = self._extract_model_tokens(response)
        
        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=model_tokens,
            raw_data=response
        )
    
    def _extract_model_tokens(self, response: Dict[str, Any]) -> List[ModelTokenInfo]:
        """Extract model-level token information from YesCode response"""
        models = []
        
        try:
            if response.get('code') != 0:
                return models
            
            subscriptions = response.get('data', [])
            if not isinstance(subscriptions, list):
                return models
            
            for sub in subscriptions:
                status = sub.get('status', 'unknown')
                if status != 'active':
                    continue
                
                group = sub.get('group', {})
                group_name = group.get('name', 'Unknown Package')
                platform = group.get('platform', 'yescode')
                
                monthly_limit = float(group.get('monthly_limit_usd', 0))
                monthly_used = float(sub.get('monthly_usage_usd', 0))
                monthly_remaining = max(0, monthly_limit - monthly_used)
                
                expires_at = sub.get('expires_at')
                expiry_date = None
                
                if expires_at:
                    try:
                        dt = datetime.fromisoformat(expires_at.replace('+08:00', ''))
                        expiry_date = dt.strftime('%Y-%m-%d')
                    except:
                        pass
                
                if monthly_limit > 0:
                    models.append(ModelTokenInfo(
                        model=platform,
                        package=group_name,
                        remaining_tokens=monthly_remaining * 100,
                        used_tokens=monthly_used * 100,
                        total_tokens=monthly_limit * 100,
                        status="active",
                        expiry_date=expiry_date
                    ))
        
        except Exception as e:
            pass
        
        return models

    def get_coding_plan(self) -> CodingPlanInfo:
        """Get coding plan information from YesCode"""
        response = self._make_yescode_request()
        return self._extract_coding_plan(response)
    
    def _extract_coding_plan(self, response: Dict[str, Any]) -> CodingPlanInfo:
        """Extract coding plan information from YesCode response"""
        try:
            if response.get('code') != 0:
                return CodingPlanInfo(
                    platform=self.get_platform_name(),
                    status="Stopped",
                    quotas=[],
                    raw_data=response
                )
            
            subscriptions = response.get('data', [])
            if not isinstance(subscriptions, list):
                return CodingPlanInfo(
                    platform=self.get_platform_name(),
                    status="Stopped",
                    quotas=[],
                    raw_data=response
                )
            
            quotas = []
            
            for sub in subscriptions:
                if sub.get('status') != 'active':
                    continue
                
                group = sub.get('group', {})
                expires_at = sub.get('expires_at')
                
                reset_timestamp = -1
                reset_time = None
                
                if expires_at:
                    try:
                        dt = datetime.fromisoformat(expires_at.replace('+08:00', ''))
                        reset_timestamp = int(dt.timestamp())
                        reset_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                daily_limit = float(group.get('daily_limit_usd', 0))
                daily_used = float(sub.get('daily_usage_usd', 0))
                
                if daily_limit > 0:
                    percent = (daily_used / daily_limit) * 100
                    quotas.append(CodingPlanQuota(
                        level='daily',
                        percent=min(100.0, percent),
                        reset_timestamp=reset_timestamp,
                        reset_time=reset_time
                    ))
                
                weekly_limit = float(group.get('weekly_limit_usd', 0))
                weekly_used = float(sub.get('weekly_usage_usd', 0))
                
                if weekly_limit > 0:
                    percent = (weekly_used / weekly_limit) * 100
                    quotas.append(CodingPlanQuota(
                        level='weekly',
                        percent=min(100.0, percent),
                        reset_timestamp=reset_timestamp,
                        reset_time=reset_time
                    ))
                
                monthly_limit = float(group.get('monthly_limit_usd', 0))
                monthly_used = float(sub.get('monthly_usage_usd', 0))
                
                if monthly_limit > 0:
                    percent = (monthly_used / monthly_limit) * 100
                    quotas.append(CodingPlanQuota(
                        level='monthly',
                        percent=min(100.0, percent),
                        reset_timestamp=reset_timestamp,
                        reset_time=reset_time
                    ))
            
            status = "Running" if quotas else "Stopped"
            
            return CodingPlanInfo(
                platform=self.get_platform_name(),
                status=status,
                quotas=quotas,
                update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                raw_data=response
            )
        
        except Exception as e:
            return CodingPlanInfo(
                platform=self.get_platform_name(),
                status="Stopped",
                quotas=[],
                raw_data=response
            )
