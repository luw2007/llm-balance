"""
DuckCoding third-party relay handler (balance query only)
"""

import os
from typing import Dict, Any, Optional, List
from .base import BasePlatformHandler, PlatformTokenInfo, ModelTokenInfo, CostInfo
from ..config import PlatformConfig


class DuckCodingHandler(BasePlatformHandler):
    """DuckCoding relay platform handler (only balance query is implemented)."""

    @classmethod
    def get_default_config(cls) -> dict:
        """Default configuration for DuckCoding balance query via cookie auth."""
        return {
            "display_name": "DuckCoding",
            "handler_class": "DuckCodingHandler",
            "description": "DuckCoding relay (balance only)",
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
            # Keep disabled by default to avoid affecting default cost runs
            "enabled": False,
            # Cookie domain where auth_token is stored
            "cookie_domain": "duckcoding.com",
            # Note: api_user_id is now loaded from environment variables or separate config
        }

    def __init__(self, config: PlatformConfig, browser: str = 'chrome'):
        super().__init__(browser)
        self.config = config
        # Load platform-specific configuration from environment variables
        self._load_env_config()

    def _load_env_config(self):
        """Load configuration from environment variables or separate config file."""
        # Try environment variable first
        env_user_id = os.getenv('DUCKCODING_API_USER_ID')
        if env_user_id:
            self.config.api_user_id = env_user_id
            return

        # Try separate config file
        import yaml
        from pathlib import Path
        config_path = Path.home() / '.llm_balance' / 'duckcoding_config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    duck_config = yaml.safe_load(f) or {}
                    if 'api_user_id' in duck_config:
                        self.config.api_user_id = duck_config['api_user_id']
            except Exception:
                pass

    def get_platform_name(self) -> str:
        return "DuckCoding"

    def get_balance(self) -> CostInfo:
        """Return cost info using quota balance and used quota from user info.

        - Balance = data.quota / 500000 (CNY)
        - Spent = data.used_quota / 500000 (CNY)
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for DuckCoding")

        headers = (self.config.headers or {}).copy()

        # Acquire cookies and auth token
        cookies = {}
        domains_to_try = []
        if getattr(self.config, 'cookie_domain', None):
            domains_to_try.append(self.config.cookie_domain)
        for d in [".duckcoding.com", "duckcoding.com"]:
            if d not in domains_to_try:
                domains_to_try.append(d)

        for domain in domains_to_try:
            try:
                cookies = self._get_cookies(domain)
                if cookies:
                    break
            except Exception:
                continue

        if not cookies:
            raise ValueError(
                f"No authentication cookies found for DuckCoding. Please ensure you are logged in to {domains_to_try[0]} in {self.browser} browser."
            )

        # Get api_user_id from config (loaded from env var or separate config file)
        api_user_id = getattr(self.config, 'api_user_id', None)
        if not api_user_id:
            raise ValueError(
                "DuckCoding requires api_user_id to be configured. Please set it using:\n"
                "1. Environment variable: export DUCKCODING_API_USER_ID=YOUR_USER_ID\n"
                "2. Separate config file: ~/.llm_balance/duckcoding_config.yaml\n"
                "   api_user_id: YOUR_USER_ID"
            )

        # Set required headers
        headers["new-api-user"] = str(api_user_id)
        if "session" in cookies:
            headers["Cookie"] = f'session={cookies["session"]}'
        # No additional auth headers needed, just use cookies directly
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            cookies=cookies
        )

        if not response:
            raise ValueError("No response from DuckCoding user API")

        # Extract balance and spent from quota data
        balance = 0.0
        spent = 0.0
        try:
            data = response.get('data', {}) if isinstance(response, dict) else {}
            quota = data.get('quota', 0)
            used_quota = data.get('used_quota', 0)
            if quota is not None:
                balance = float(quota) / 500000.0
            if used_quota is not None:
                spent = float(used_quota) / 500000.0
        except Exception:
            balance = 0.0
            spent = 0.0

        return CostInfo(
            platform=self.get_platform_name(),
            balance=balance,
            currency='CNY',
            spent=spent,
            spent_currency='CNY',
            raw_data=response
        )

    def get_model_tokens(self) -> PlatformTokenInfo:
        """Query DuckCoding user info and create usage package from quota data.

        Authentication:
            - Use cookies from duckcoding.com domain
            - No additional auth headers required

        Data source:
            - GET https://duckcoding.com/api/user/self
            - Use data.quota and data.used_quota from response

        Models:
            - Generic model name: "DuckCoding Models"
            - Package name: "DuckCoding 按量计费(不到期)"
        """
        if not getattr(self.config, 'api_url', None):
            raise ValueError("No API URL configured for DuckCoding")

        headers = (self.config.headers or {}).copy()

        # Acquire cookies from the configured domain
        cookies = {}
        domains_to_try = []
        if getattr(self.config, 'cookie_domain', None):
            domains_to_try.append(self.config.cookie_domain)
        for d in [".duckcoding.com", "duckcoding.com"]:
            if d not in domains_to_try:
                domains_to_try.append(d)

        for domain in domains_to_try:
            try:
                cookies = self._get_cookies(domain)
                if cookies:
                    break
            except Exception:
                continue

        if not cookies:
            raise ValueError(
                f"No authentication cookies found for DuckCoding. Please ensure you are logged in to {domains_to_try[0]} in {self.browser} browser."
            )

        # Get api_user_id from config (loaded from env var or separate config file)
        api_user_id = getattr(self.config, 'api_user_id', None)
        if not api_user_id:
            raise ValueError(
                "DuckCoding requires api_user_id to be configured. Please set it using:\n"
                "1. Environment variable: export DUCKCODING_API_USER_ID=YOUR_USER_ID\n"
                "2. Separate config file: ~/.llm_balance/duckcoding_config.yaml\n"
                "   api_user_id: YOUR_USER_ID"
            )

        # Set required headers
        headers["new-api-user"] = str(api_user_id)
        if "session" in cookies:
            headers["Cookie"] = f'session={cookies["session"]}'

        # Make the user info request
        response = self._make_request(
            url=self.config.api_url,
            method=self.config.method,
            headers=headers,
            cookies=cookies
        )

        if not response:
            raise ValueError("No response from DuckCoding user API")

        # Extract quota information
        total_quota = 0.0
        used_quota = 0.0
        try:
            data = response.get('data', {}) if isinstance(response, dict) else {}
            quota = data.get('quota', 0)
            used_quota_data = data.get('used_quota', 0)
            if quota is not None:
                total_quota = float(quota)
            if used_quota_data is not None:
                used_quota = float(used_quota_data)
        except Exception:
            total_quota = 0.0
            used_quota = 0.0

        # Calculate remaining quota
        remaining_quota = max(0.0, total_quota - used_quota)

        # Create model info
        model_info = ModelTokenInfo(
            model="DuckCoding Models",
            package="DuckCoding 按量计费",
            remaining_tokens=remaining_quota,
            used_tokens=used_quota,
            total_tokens=total_quota
        )

        return PlatformTokenInfo(
            platform=self.get_platform_name(),
            models=[model_info],
            raw_data=response
        )
