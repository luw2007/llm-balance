"""
YourAPI third-party relay handler
"""

from typing import Dict, Any, Optional, List
from .relay import RelayPlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class YourAPIHandler(RelayPlatformHandler):
    """YourAPI relay platform handler."""

    platform_id = 'YOURAPI'
    user_id_header = 'new-api-user'
    quota_scaling = 500000.0

    @classmethod
    def get_default_config(cls) -> dict:
        """Default configuration for YourAPI."""
        return {
            "display_name": "YourAPI",
            "handler_class": "YourAPIHandler",
            "description": "YourAPI relay (balance and package)",
            "api_url": "https://yourapi.cn/api/user/self",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": None,
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            },
            "params": {},
            "data": {},
            "enabled": False,
            "cookie_domain": "yourapi.cn"
        }

    def get_platform_name(self) -> str:
        return "YourAPI"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Query YourAPI user data and create usage package from quota info."""
        response = self._make_relay_request()

        # Extract quota information
        total_quota = 0.0
        used_quota = 0.0
        try:
            data = response.get('data', {})
            total_quota = float(data.get('quota', 0))
            used_quota = float(data.get('used_quota', 0))
        except Exception:
            pass

        model_info = ModelTokenInfo(
            model="gpt-4,gpt-3.5-turbo,claude",
            package="YourAPI Quota Package",
            remaining_tokens=max(0.0, total_quota - used_quota),
            used_tokens=used_quota,
            total_tokens=total_quota,
            status="active"
        )

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=[model_info],
            raw_data=response
        )
