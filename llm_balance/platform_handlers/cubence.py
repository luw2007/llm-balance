"""
Cubence platform handler
"""

import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo
from ..config import PlatformConfig


class CubenceHandler(BasePlatformHandler):
    """Cubence platform cost handler"""

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for Cubence platform"""
        return {
            "api_url": "https://cubence.com/api/v1/dashboard/overview",
            "method": "GET",
            "auth_type": "token",
            "env_var": "CUBENCE_TOKEN",
            "token": None,  # Will be set from environment or config file
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Content-Type": "application/json",
                "DNT": "1",
                "Referer": "https://cubence.com/dashboard",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            },
            "params": {},
            "data": {},
            "enabled": True,
            "show_cost": True,
            "show_package": False,  # 暂时不支持订阅模型
            "display_name": "Cubence",
            "description": "Cubence AI platform"
        }

    def __init__(self, config, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        # Load platform-specific configuration from environment variables or separate config file
        self._load_env_config()

    def _load_env_config(self):
        """Load configuration from environment variables or separate config file."""
        # Try environment variable first
        env_token = os.getenv('CUBENCE_TOKEN')
        if env_token:
            self.config.token = env_token
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'cubence_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cubence_config = yaml.safe_load(f) or {}
                    if 'token' in cubence_config:
                        self.config.token = cubence_config['token']
            except Exception as e:
                pass

    def get_balance(self) -> CostInfo:
        """Get cost information from Cubence"""
        api_url = self.config.get('api_url') if isinstance(self.config, dict) else self.config.api_url
        if not api_url:
            raise ValueError("No API URL configured for Cubence")

        # Get token from configuration
        token = getattr(self.config, 'token', None)
        if not token:
            raise ValueError(
                "Cubence token required. Please set it using one of the following methods:\n"
                "1. Environment variable: export CUBENCE_TOKEN='your_token'\n"
                "2. Config file: llm-balance platform_config cubence token 'your_token'\n"
                "3. Or create ~/.llm_balance/cubence_config.yaml with:\n"
                "   token: your_token"
            )

        # Prepare authentication headers
        headers = self.config.headers.copy() if hasattr(self.config, 'headers') else self.config.get('headers', {}).copy()

        # Set token as cookie (Cubence uses cookie-based token authentication)
        cookies = {
            'token': token
        }

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
            raise ValueError("No response from Cubence API")

        # Extract balance and currency from response
        balance = self._extract_balance(response)
        currency = self._extract_currency(response)

        # Calculate spent amount (if available)
        spent = self._calculate_spent_amount(response)

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'CNY',
            spent=spent,
            spent_currency=currency or 'CNY',
            raw_data=response
        )

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "Cubence"

    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from Cubence API response

        Expected response format:
        {
            "data": {
                "balance": {
                    "normal_balance": 65500000,
                    "normal_balance_dollar": 65.5,
                    "subscription_balance": 0,
                    "subscription_balance_dollar": 0,
                    "total_balance": 65500000,
                    "total_balance_dollar": 65.5
                }
            },
            "success": true
        }

        Note: Despite the field name 'balance_dollar', the actual currency is CNY (人民币).
        The 'balance' field uses a scaled integer (divide by 1000000), while
        'balance_dollar' already provides the decimal value in CNY.
        """
        try:
            # Extract balance from response
            if 'data' in response and 'balance' in response['data']:
                balance_data = response['data']['balance']

                # Use total_balance_dollar field (already in decimal CNY despite the name)
                if 'total_balance_dollar' in balance_data:
                    return float(balance_data['total_balance_dollar'])

                # Fallback to normal_balance_dollar
                if 'normal_balance_dollar' in balance_data:
                    return float(balance_data['normal_balance_dollar'])

                # Fallback to total_balance (in scaled units, divide by 1000000)
                if 'total_balance' in balance_data:
                    return float(balance_data['total_balance']) / 1000000

                # Fallback to normal_balance (in scaled units, divide by 1000000)
                if 'normal_balance' in balance_data:
                    return float(balance_data['normal_balance']) / 1000000

            return None

        except (ValueError, TypeError, KeyError) as e:
            print(f"Warning: Failed to extract balance from Cubence response: {e}")
            return None

    def _extract_currency(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract currency from Cubence API response

        Note: Although the field is named 'balance_dollar', Cubence actually charges in CNY (人民币)
        """
        # Cubence charges in CNY despite the field name
        return 'CNY'

    def _calculate_spent_amount(self, response: Dict[str, Any]) -> float:
        """Calculate spent amount from Cubence API response

        Note: This may not be available in the overview endpoint.
        Return "-" string to indicate not supported, or 0.0 if truly no spending.
        """
        try:
            # Try common spent/used field locations
            if 'data' in response:
                data = response['data']

                # Try direct spent field
                if 'spent' in data:
                    return float(data['spent'])

                # Try used amount field
                if 'used_amount' in data:
                    return float(data['used_amount'])

                # Try total cost field
                if 'total_cost' in data:
                    return float(data['total_cost'])

                # Try wallet spent field
                if 'wallet' in data and isinstance(data['wallet'], dict):
                    if 'spent' in data['wallet']:
                        return float(data['wallet']['spent'])

            # If no spent field found, return "-" to indicate not available
            return "-"

        except (ValueError, TypeError, KeyError):
            return "-"
