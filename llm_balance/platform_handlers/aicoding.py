"""
AICoding platform handler
"""

import os
from typing import Dict, Any, Optional
from .base import BasePlatformHandler, CostInfo, ModelTokenInfo, PlatformTokenInfo
from ..config import PlatformConfig


class AICodingHandler(BasePlatformHandler):
    """AICoding platform cost handler"""

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for AICoding platform"""
        return {
            "api_url": "https://aicoding.sh/api/user-credits/permanent",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "DNT": "1",
                "Referer": "https://aicoding.sh/console/credits",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            },
            "cookie_domain": "aicoding.sh",
            "params": {},
            "data": {},
            "enabled": True,
            "show_cost": True,
            "show_package": True,
            "display_name": "AICoding",
            "description": "AICoding AI platform"
        }

    def __init__(self, config, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config

    def get_balance(self) -> CostInfo:
        """Get cost information from AICoding"""
        api_url = self.config.get('api_url') if isinstance(self.config, dict) else self.config.api_url
        if not api_url:
            raise ValueError("No API URL configured for AICoding")

        # Prepare headers
        headers = self.config.headers.copy() if hasattr(self.config, 'headers') else self.config.get('headers', {}).copy()

        # Get cookies from browser
        cookie_domain = getattr(self.config, 'cookie_domain', 'aicoding.sh')
        cookies = self._get_cookies(cookie_domain)

        # Make API request
        response = self._make_request(
            url=api_url,
            method='GET',
            headers=headers,
            cookies=cookies
        )

        if not response:
            raise ValueError("No response from AICoding API")

        # Extract balance from response
        balance = self._extract_balance(response)
        currency = 'CNY'

        # Calculate spent amount (not available from this API)
        spent = "-"

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
        return "AICoding"

    def _extract_balance(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract balance from AICoding API response

        Expected response format:
        {
            "personal_credits": 1234,
            ...
        }

        Balance calculation: personal_credits / 100 = CNY
        """
        try:
            personal_credits = response.get('personal_credits', 0)
            return float(personal_credits) / 100

        except (ValueError, TypeError, KeyError) as e:
            print(f"Warning: Failed to extract balance from AICoding response: {e}")
            return None

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get credits-based token information from AICoding"""
        api_url = self.config.get('api_url') if isinstance(self.config, dict) else self.config.api_url
        if not api_url:
            raise ValueError("No API URL configured for AICoding")

        headers = self.config.headers.copy() if hasattr(self.config, 'headers') else self.config.get('headers', {}).copy()

        cookie_domain = getattr(self.config, 'cookie_domain', 'aicoding.sh')
        cookies = self._get_cookies(cookie_domain)

        response = self._make_request(
            url=api_url,
            method='GET',
            headers=headers,
            cookies=cookies
        )

        if not response:
            raise ValueError("No response from AICoding API")

        personal_credits = float(response.get('personal_credits', 0))

        models = [
            ModelTokenInfo(
                model="Credits",
                package="AICoding",
                total_tokens=personal_credits,
                used_tokens=0,
                remaining_tokens=personal_credits,
                status="active"
            )
        ]

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=models,
            raw_data=response
        )
