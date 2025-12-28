"""
IKunCode platform handler
"""

from typing import Dict, Any, Optional, List
from .relay import RelayPlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class IKunCodeHandler(RelayPlatformHandler):
    """IKunCode platform cost handler"""

    platform_id = 'IKUNCODE'
    user_id_header = 'new-api-user'
    quota_scaling = 500000.0

    @classmethod
    def get_default_config(cls) -> dict:
        """Get default configuration for IKunCode platform"""
        return {
            "api_url": "https://api.ikuncode.cc/api/user/self",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": "IKUNCODE_API_USER_ID",
            "api_user_id": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "DNT": "1",
                "Referer": "https://api.ikuncode.cc/topup",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            },
            "cookie_domain": "api.ikuncode.cc",
            "params": {},
            "data": {},
            "enabled": False,
            "show_cost": True,
            "show_package": True,
            "display_name": "IKunCode",
            "description": "IKunCode AI platform"
        }

    def get_platform_name(self) -> str:
        """Get platform display name"""
        return "IKunCode"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Get quota-based token information from IKunCode"""
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
                package="IKunCode",
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
