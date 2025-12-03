"""
Magic666 platform handler
"""

import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo, ModelTokenInfo, PlatformTokenInfo
from ..config import PlatformConfig


class Magic666Handler(BasePlatformHandler):
    """Magic666 platform cost handler"""

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Magic666 platform"""
        return {
            "api_url": "https://magic666.top/api/user/self",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": "MAGIC666_API_USER_ID",
            "api_user_id": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "DNT": "1",
                "Referer": "https://magic666.top/console/topup",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            },
            "cookie_domain": "magic666.top",
            "params": {},
            "data": {},
            "enabled": False,
            "show_cost": True,
            "show_package": True,
            "display_name": "Magic666",
            "description": "Magic666 AI platform"
        }

    def __init__(self, config, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        self._load_env_config()

    def _load_env_config(self):
        """Load configuration from environment variables or separate config file."""
        # Try environment variable first
        env_user_id = os.getenv('MAGIC666_API_USER_ID')
        if env_user_id:
            self.config.api_user_id = env_user_id
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'magic666_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    platform_config = yaml.safe_load(f) or {}
                    if 'api_user_id' in platform_config:
                        self.config.api_user_id = platform_config['api_user_id']
            except Exception:
                pass

    def get_balance(self) -> CostInfo:
        """Get cost information from Magic666"""
        api_url = self.config.get('api_url') if isinstance(self.config, dict) else self.config.api_url
        if not api_url:
            raise ValueError("No API URL configured for Magic666")

        # Get api_user_id from configuration
        api_user_id = getattr(self.config, 'api_user_id', None)
        if not api_user_id:
            raise ValueError(
                "Magic666 api_user_id required. Please set it using one of the following methods:\n"
                "1. Environment variable: export MAGIC666_API_USER_ID='your_user_id'\n"
                "2. Config file: llm-balance platform_config magic666 api_user_id 'your_user_id'\n"
                "3. Or create ~/.llm_balance/magic666_config.yaml with:\n"
                "   api_user_id: your_user_id"
            )

        # Prepare headers
        headers = self.config.headers.copy() if hasattr(self.config, 'headers') else self.config.get('headers', {}).copy()
        headers['new-api-user'] = str(api_user_id)

        # Get cookies from browser
        cookie_domain = getattr(self.config, 'cookie_domain', 'magic666.top')
        cookies = self._get_cookies(cookie_domain)

        # Make API request
        method = self.config.method if hasattr(self.config, 'method') else self.config.get('method', 'GET')
        params = self.config.params if hasattr(self.config, 'params') else self.config.get('params', {})
        data = self.config.data if hasattr(self.config, 'data') else self.config.get('data', {})

        response = self._make_request(
            url=api_url,
            method=method,
            headers=headers,
            cookies=cookies,
            params=params,
            data=data
        )

        if not response:
            raise ValueError("No response from Magic666 API")

        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = 'CNY'

        # Calculate spent amount
        spent = self._calculate_spent_amount(response)

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency,
            spent=spent,
            spent_currency=currency,
            raw_data=response
        )

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Magic666"

    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Magic666 API response

        Expected response format:
        {
            "data": {
                "quota": 25000000,
                "bonus_quota": 241522,
                "used_quota": 8478,
                ...
            },
            "success": true
        }

        Balance calculation: (quota + bonus_quota) / 500000 = CNY
        """
        try:
            if 'data' in response:
                data = response['data']
                quota = float(data.get('quota', 0))
                bonus_quota = float(data.get('bonus_quota', 0))
                total_quota = quota + bonus_quota
                return total_quota / 500000

            return None

        except (ValueError, TypeError, KeyError) as e:
            print(f"Warning: Failed to extract balance from Magic666 response: {e}")
            return None

    def _calculate_spent_amount(self, response: Dict[str, Any]) -> float:
        """Calculate spent amount from Magic666 API response

        Spent calculation: used_quota / 500000 = CNY
        """
        try:
            if 'data' in response:
                data = response['data']
                used_quota = float(data.get('used_quota', 0))
                return used_quota / 500000

            return "-"

        except (ValueError, TypeError, KeyError):
            return "-"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get quota-based token information from Magic666

        Returns quota info as a single model entry showing total/used/remaining.
        """
        api_url = self.config.get('api_url') if isinstance(self.config, dict) else self.config.api_url
        if not api_url:
            raise ValueError("No API URL configured for Magic666")

        api_user_id = getattr(self.config, 'api_user_id', None)
        if not api_user_id:
            raise ValueError("Magic666 api_user_id required")

        headers = self.config.headers.copy() if hasattr(self.config, 'headers') else self.config.get('headers', {}).copy()
        headers['new-api-user'] = str(api_user_id)

        cookie_domain = getattr(self.config, 'cookie_domain', 'magic666.top')
        cookies = self._get_cookies(cookie_domain)

        response = self._make_request(
            url=api_url,
            method='GET',
            headers=headers,
            cookies=cookies
        )

        if not response or 'data' not in response:
            raise ValueError("No response from Magic666 API")

        data = response['data']
        quota = float(data.get('quota', 0))
        bonus_quota = float(data.get('bonus_quota', 0))
        used_quota = float(data.get('used_quota', 0))

        total_tokens = quota + bonus_quota
        remaining_tokens = total_tokens - used_quota

        models = [
            ModelTokenInfo(
                model="Quota",
                package="Magic666",
                total_tokens=total_tokens,
                used_tokens=used_quota,
                remaining_tokens=remaining_tokens,
                status="active"
            )
        ]

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=models,
            raw_data=response
        )
