"""
AICoding platform handler
"""

from typing import Dict, Any, Optional, List
from .relay import RelayPlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class AICodingHandler(RelayPlatformHandler):
    """AICoding platform cost handler"""

    user_id_header = None # No user id header needed

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
            "enabled": False,
            "show_cost": True,
            "show_package": True,
            "display_name": "AICoding",
            "description": "AICoding AI platform"
        }

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "AICoding"

    def get_balance(self) -> CostInfo:
        """Get cost information from AICoding"""
        response = self._make_relay_request()
        
        # Balance calculation: personal_credits / 100 = CNY
        personal_credits = float(response.get('personal_credits', 0))
        balance = personal_credits / 100.0

        return CostInfo(
            platform=self.get_platform_name(),
            balance=self._validate_balance(balance),
            currency='CNY',
            spent="-",
            spent_currency='CNY',
            raw_data=response
        )

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get credits-based token information from AICoding"""
        response = self._make_relay_request()
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
