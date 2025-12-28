"""
88996 platform handler
"""

from typing import Dict, Any, Optional, List
from .relay import RelayPlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class Handler88996(RelayPlatformHandler):
    """88996 platform cost handler"""

    platform_id = 'CLOUD88996'
    user_id_header = 'rix-api-user'
    quota_scaling = 500000.0

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for 88996 platform"""
        return {
            "api_url": "https://88996.cloud/api/user/self",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": "CLOUD88996_API_USER_ID",
            "api_user_id": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "DNT": "1",
                "Referer": "https://88996.cloud/topup",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            },
            "cookie_domain": "88996.cloud",
            "params": {},
            "data": {},
            "enabled": False,
            "show_cost": True,
            "show_package": True,
            "display_name": "88996",
            "description": "88996 AI platform"
        }

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "88996"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get quota-based token information from 88996"""
        response = self._make_relay_request()

        data = response.get('data', {})
        quota = float(data.get('quota', 0))
        bonus_quota = float(data.get('bonus_quota', 0))
        used_quota = float(data.get('used_quota', 0))

        total_tokens = quota + bonus_quota
        remaining_tokens = total_tokens - used_quota

        models = [
            ModelTokenInfo(
                model="Quota",
                package="88996",
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
