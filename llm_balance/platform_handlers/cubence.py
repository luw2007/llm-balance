"""
Cubence platform handler
"""

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
            "auth_type": "cookie",
            "cookie_domain": "cubence.com",
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
            "enabled": False,
            "show_cost": True,
            "show_package": False,  # 暂时不支持订阅模型
            "display_name": "Cubence",
            "description": "Cubence AI platform"
        }

    def __init__(self, config, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config

    def get_balance(self) -> CostInfo:
        """Get cost information from Cubence"""
        api_url = self.config.get('api_url') if isinstance(self.config, dict) else self.config.api_url
        if not api_url:
            raise ValueError("No API URL configured for Cubence")

        # Get cookies from browser
        cookie_domain = getattr(self.config, 'cookie_domain', 'cubence.com')
        cookies = self._get_cookies(cookie_domain, silent=False)

        if not cookies:
            raise ValueError(
                f"Failed to retrieve cookies from browser for domain: {cookie_domain}\n"
                "Please ensure you are logged in to Cubence in your browser."
            )

        # Prepare authentication headers
        headers = self.config.headers.copy() if hasattr(self.config, 'headers') else self.config.get('headers', {}).copy()

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

        # Set spent_currency based on whether spent is available
        spent_currency = currency or 'CNY' if spent != "-" else "-"

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance or 0.0,
            currency=currency or 'CNY',
            spent=spent,
            spent_currency=spent_currency,
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

        Expected response format from /api/v1/dashboard/overview:
        {
            "data": {
                "apikey_stats": {
                    "active": 1,
                    "quota_limit": -1,
                    "quota_used": 3182440,  # Total quota used across all API keys
                    "total": 1
                },
                ...
            },
            "success": true
        }

        Spent calculation: quota_used / 1000000 = CNY
        (Same scaling as balance: 1M tokens = 1 CNY)
        """
        try:
            # Extract spent from apikey_stats
            if 'data' in response:
                data = response['data']

                # Try apikey_stats.quota_used (from dashboard/overview endpoint)
                if 'apikey_stats' in data and isinstance(data['apikey_stats'], dict):
                    apikey_stats = data['apikey_stats']
                    if 'quota_used' in apikey_stats:
                        quota_used = apikey_stats['quota_used']
                        try:
                            # Convert using same scaling as balance (1M tokens = 1 CNY)
                            spent = float(quota_used) / 1000000.0
                            return spent
                        except (ValueError, TypeError):
                            pass

                # Fallback: Try direct spent field (for potential future API changes)
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
