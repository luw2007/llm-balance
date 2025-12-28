"""
DuckCoding third-party relay handler
"""

from typing import Dict, Any, Optional, List
from .relay import RelayPlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class DuckCodingHandler(RelayPlatformHandler):
    """DuckCoding relay platform handler."""

    platform_id = 'DUCKCODING'
    user_id_header = 'new-api-user'
    quota_scaling = 500000.0

    @classmethod
    def get_default_config(cls) -> dict:
        """Default configuration for DuckCoding."""
        return {
            "display_name": "DuckCoding",
            "handler_class": "DuckCodingHandler",
            "description": "DuckCoding relay (balance and package)",
            "api_url": "https://duckcoding.com/api/user/self",
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
            "cookie_domain": "duckcoding.com",
        }

    def get_platform_name(self) -> str:
        return "DuckCoding"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Query DuckCoding user info and create usage package from quota data."""
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

        remaining_quota = max(0.0, total_quota - used_quota)

        model_info = ModelTokenInfo(
            model="claude,codex",
            package="DuckCoding 按量计费",
            remaining_tokens=remaining_quota,
            used_tokens=used_quota,
            total_tokens=total_quota,
            status="active"
        )

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=[model_info],
            raw_data=response
        )
