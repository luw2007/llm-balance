"""
PackyCode third-party relay handler
"""

from typing import Dict, Any, Optional, List
from .relay import RelayPlatformHandler, CostInfo, PlatformTokenInfo, ModelTokenInfo
from ..config import PlatformConfig

class PackyCodeHandler(RelayPlatformHandler):
    """PackyCode relay platform handler."""

    platform_id = 'PACKYCODE'
    user_id_header = 'new-api-user'
    quota_scaling = 500000.0

    @classmethod
    def get_default_config(cls) -> dict:
        """Default configuration for PackyCode."""
        return {
            "display_name": "PackyCode",
            "handler_class": "PackyCodeHandler",
            "description": "PackyCode relay (balance and package)",
            "api_url": "https://packyapi.com/api/user/self",
            "official_url": "https://www.packyapi.com",
            "api_management_url": "https://www.packyapi.com/console/topup",
            "method": "GET",
            "auth_type": "cookie",
            "env_var": "PACKYCODE_API_USER_ID",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            },
            "params": {},
            "data": {},
            "setup_steps": [
                '访问 https://www.packyapi.com 并登录',
                '进入 "控制台" → "充值" 页面获取 api_user_id',
                '或者查看页面请求头中的 new-api-user 字段',
                '在浏览器中保持登录状态',
                '设置环境变量: export PACKYCODE_API_USER_ID="your_user_id"'
            ],
            "notes": [
                '使用浏览器cookie认证',
                '需要设置 PACKYCODE_API_USER_ID 环境变量',
                '工具会自动读取浏览器中的 packyapi.com 相关的 cookie'
            ],
            "enabled": False,
            "cookie_domain": "packyapi.com",
        }

    def get_platform_name(self) -> str:
        return "PackyCode"

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Query PackyCode user info and create usage package from quota data."""
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
            package="PackyCode 按量计费",
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
